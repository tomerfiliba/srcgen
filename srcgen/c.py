from __future__ import with_statement
from contextlib import contextmanager


class CModule(object):
    def __init__(self, name = None, line_width = 80):
        self.name = name
        self.line_width = line_width
        self._curr = []
    def __repr__(self):
        return "CModule(%r)" % (self.name,)
    def __str__(self):
        return self.render()
    
    @classmethod
    def _render(cls, curr, level):
        indent = "    " * level
        for elem in curr:
            if isinstance(elem, list):
                for line in cls._render(elem, level + 1):
                    yield line
            else:
                yield indent + str(elem)
    def render(self):
        return "\n".join(self._render(self._curr, 0))
        
    def dump(self, filename_or_fileobj):
        """Renders the module and dumps it to the given file. ``file`` can be either a file name or 
        a file object"""
        data = self.render()
        if hasattr(filename_or_fileobj, "write"):
            filename_or_fileobj.write(data)
        else:
            with open(filename_or_fileobj, "w") as f:
                f.write(data)

    #
    # Separator and Comment
    #
    def sep(self, count = 1):
        self._curr.extend("" for _ in range(count))
    def comment(self, *lines, **kwargs):
        box = kwargs.pop("box", False)
        sep = kwargs.pop("sep", False)
        if sep and box:
            self._curr.append("")
            self._curr.append("/* " + "*" * (self.line_width-2))
        elif sep:
            self._curr.append("/*")
        elif box:
            self._curr.append("/* " + "*" * (self.line_width-2))
        self._curr.extend("/* %s" % (l.replace("*/", "* /"),) for l in "\n".join(lines).splitlines())
        if sep and box:
            self._curr.append("*" * (self.line_width - 2) + " */")
            self._curr.append("")
        elif sep:
            self._curr.append("*/")
        elif box:
            self._curr.append("*" * (self.line_width - 2) + " */")
        else:
            self._curr[-1] += " */"
    
    #
    # Statements
    #
    def stmt(self, text, *args, **kwargs):
        text = str(text)
        semicolon = kwargs.pop("semicolon", True)
        if kwargs:
            raise TypeError("Invalid keyword argument %r" % (kwargs.keys(),))
        if semicolon and text.strip()[0] != "#" and text[-1] not in ";:{":
            text += ";"
        self._curr.append(text.format(*args) if args else text)
    def break_(self):
        self.stmt("break")
    def continue_(self):
        self.stmt("continue")
    def return_(self, expr, *args):
        self.stmt("return %s" % (expr,), *args)
    def goto(self, name):
        self.stmt("goto %s" % (name,))
    def label(self, name):
        self.stmt("%s:" % (name,))
    
    def include(self, filename):
        if filename.startswith("<"):
            self.stmt("#include %s" % (filename,))
        else:
            self.stmt('#include "%s"' % (filename,))
    def define(self, name, value = None):
        if value:
            value = value.replace("\n", "\\\n")
            self.stmt("#define %s %s" % (name, value))
        else:
            self.stmt("#define %s" % (name,))
    
    #
    # Suites
    #
    @contextmanager
    def suite(self, headline, *args, **kwargs):
        headline = str(headline)
        terminator = kwargs.pop("terminator", None)
        if kwargs:
            raise TypeError("Invalid keyword argument %r" % (kwargs.keys(),))
        if headline[-1] not in "{:":
            headline += " {"
        self._curr.append(headline.format(*args) if args else headline)
        prev = self._curr
        self._curr = []
        prev.append(self._curr)
        yield
        self._curr = prev
        if not terminator:
            self._curr.append("}")
        else:
            self._curr.append(terminator)
        
    @contextmanager
    def if_(self, cond, *args):
        with self.suite("if (%s)" % (cond,), *args): yield
    @contextmanager
    def elif_(self, cond, *args):
        with self.suite("else if (%s)" % (cond,), *args): yield
    @contextmanager
    def else_(self):
        with self.suite("else"): yield
    @contextmanager
    def for_(self, init, cond, next):
        with self.suite("for (%s; %s, %s)" % (init, cond, next)): yield
    @contextmanager
    def while_(self, cond, *args):
        with self.suite("while %s:" % (cond,), *args): yield
    @contextmanager
    def do_while(self, cond, *args):
        with self.suite("do", terminator = "} while(%s);" % (cond,), *args): yield

    @contextmanager
    def switch(self, cond, *args):
        with self.suite("switch (%s)" % (cond,),  *args): yield
    @contextmanager
    def case(self, val, *args):
        with self.suite("case (%s):" % (val,),  *args): yield
    @contextmanager
    def default(self):
        with self.suite("default:"): yield
        
    @contextmanager
    def func(self, type, name, *args):
        with self.suite("%s %s(%s)" % (type, name, ", ".join(str(a) for a in args))): yield
        self.sep()
    
    @contextmanager
    def struct(self, name, varname = None):
        with self.suite("struct %s" % (name,), terminator = "} %s;" % (varname,) if varname else "};"): yield
        self.sep()
    @contextmanager
    def union(self, name, varname = None):
        with self.suite("union %s" % (name,), terminator = "} %s;" % (varname,) if varname else "};"): yield
        self.sep()
    @contextmanager
    def enum(self, name, varname = None):
        with self.suite("enum %s" % (name,), terminator = "} %s;" % (varname,) if varname else "};"):
            yield 
            if self._curr[-1].endswith(","):
                self._curr[-1] = self._curr[-1][:-1]
        self.sep()
    def enum_member(self, name, value = None):
        self._curr.append("%s = %s," % (name, value) if value is not None else "%s," % (name,))
    
    @contextmanager
    def typedef(self, type, name):
        self.stmt("typedef %s %s" % (type, name))
    @contextmanager
    def typedef_struct(self, name):
        with self.suite("typedef struct _%s" % (name,), terminator = "} %s;" % (name,)): yield
        self.sep()
    @contextmanager
    def typedef_union(self, name):
        with self.suite("typedef union _%s" % (name,), terminator = "} %s;" % (name,)): yield
        self.sep()
    @contextmanager
    def typedef_enum(self, name):
        with self.suite("typedef enum _%s" % (name,), terminator = "} %s;" % (name,)): yield
        self.sep()


def R(*args, **kwargs):
    """repr"""
    if args and kwargs:
        raise TypeError("Either positional or keyword arguments may be given")
    elif args:
        if len(args) != 1:
            raise TypeError("Exactly one positional argument may be given")
        return repr(args[0])
    elif kwargs:
        if len(kwargs) != 1:
            raise TypeError("Exactly one keyword argument may be given")
        return "%s = %r" % kwargs.popitem()
    else:
        raise TypeError("Either positional or keyword arguments must be given")

class E(object):
    """
    Expression object
    """
    __slots__ = ["_value"]
    def __init__(self, value):
        self._value = str(value)
    def __str__(self):
        return self._value
    def __repr__(self):
        return self._value
    
    def __add__(self, other):
        return E("(%r + %r)" % (self, other))
    def __sub__(self, other):
        return E("(%r - %r)" % (self, other))
    def __mul__(self, other):
        return E("(%r * %r)" % (self, other))
    def __truediv__(self, other):
        return E("(%r / %r)" % (self, other))
    __div__ = __truediv__
    def __mod__(self, other):
        return E("(%r % %r)" % (self, other))
    def __pow__(self, other):
        return E("(%r % %r)" % (self, other))
    def __or__(self, other):
        return E("(%r | %r)" % (self, other))
    def __and__(self, other):
        return E("(%r & %r)" % (self, other))
    def __xor__(self, other):
        return E("(%r ^ %r)" % (self, other))
    def __lshift__(self, other):
        return E("(%r << %r)" % (self, other))
    def __rshift__(self, other):
        return E("(%r >> %r)" % (self, other))

    def __radd__(self, other):
        return E("(%r + %r)" % (other, self))
    def __rsub__(self, other):
        return E("(%r - %r)" % (other, self))
    def __rmul__(self, other):
        return E("(%r * %r)" % (other, self))
    def __rtruediv__(self, other):
        return E("(%r / %r)" % (other, self))
    __rdiv__ = __rtruediv__
    def __rmod__(self, other):
        return E("(%r % %r)" % (other, self))
    def __rpow__(self, other):
        return E("(%r % %r)" % (other, self))
    def __ror__(self, other):
        return E("(%r or %r)" % (other, self))
    def __rand__(self, other):
        return E("(%r and %r)" % (other, self))
    def __rxor__(self, other):
        return E("(%r ^ %r)" % (other, self))
    def __rlshift__(self, other):
        return E("(%r << %r)" % (other, self))
    def __rrshift__(self, other):
        return E("(%r >> %r)" % (other, self))
    
    def __gt__(self, other):
        return E("(%r > %r)" % (self, other))
    def __ge__(self, other):
        return E("(%r >= %r)" % (self, other))
    def __lt__(self, other):
        return E("(%r < %r)" % (self, other))
    def __le__(self, other):
        return E("(%r <= %r)" % (self, other))
    def __eq__(self, other):
        return E("(%r == %r)" % (self, other))
    def __ne__(self, other):
        return E("(%r != %r)" % (self, other))
    
    def __neg__(self):
        return E("-%r" % (self,))
    def __pos__(self):
        return E("+%r" % (self,))
    def __inv__(self):
        return E("~%r" % (self,))
    __invert__ = __inv__
    
    def __getitem__(self, key):
        return E("%r[%r]" % (self, key))
    def __getattr__(self, name):
        return E("%r.%s" % (self, name))
    def __call__(self, *args):
        return E("%r(%s)" % (self, ", ".join(repr(a) for a in args)))


#if __name__ == "__main__":
#    m = CModule("foo")
#    m.include("<stdio.h>")
#    m.include("<inttypes.h>")
#    m.sep()
#    m.comment("this is a simple comment")
#    with m.enum("weekdays"):
#        m.enum_member("sun")
#        m.enum_member("mon")
#        m.enum_member("tue")
#        m.enum_member("wed")
#    
#    m.comment("this is a boxed comment", box = True)
#    with m.typedef_union("foo"):
#        with m.struct("", "raw"):
#            m.stmt("uint64_t a")
#            m.stmt("uint64_t b")
#            m.stmt("uint64_t c")
#            m.stmt("uint64_t d")
#    
#    m.comment("this is a sep comment", sep = True)
#    with m.func("int", "main", "int argv", "const char ** argc"):
#        with m.if_(E("x") > 5):
#            m.stmt(E("printf")("hi"))
#    
#    print m






