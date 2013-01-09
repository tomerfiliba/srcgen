from __future__ import with_statement
from contextlib import contextmanager
import pickle


class PythonModule(object):
    def __init__(self, name, line_width = 80):
        self.name = name
        self.line_width = line_width
        self._curr = []
    def __repr__(self):
        return "PythonModule(%r)" % (self.name,)
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
            self._curr.append("#" * self.line_width)
        elif sep:
            self._curr.append("#")
        elif box:
            self._curr.append("#" * self.line_width)
        self._curr.extend("# %s" % (l,) for l in "\n".join(lines).splitlines())
        if sep and box:
            self._curr.append("#" * self.line_width)
            self._curr.append("")
        elif sep:
            self._curr.append("#")
        elif box:
            self._curr.append("#" * self.line_width)    
    
    #
    # Statements
    #
    def stmt(self, text, *args):
        self._curr.append(text.format(*args) if args else text)
    def break_(self):
        self.stmt("break")
    def continue_(self):
        self.stmt("continue")
    def return_(self, expr, *args):
        self.stmt("return %s" % (expr,), *args)
    def yield_(self, expr, *args):
        self.stmt("yield %s" % (expr,), *args)
    def raise_(self, expr, *args):
        self.stmt("raise %s" % (expr,), *args)
    def import_(self, modname):
        self.stmt("import %s" % (modname,))
    def from_(self, modname, *attrs):
        self.stmt("from %s import %s" % (modname, ", ".join(attrs)))
    
    #
    # Suites
    #
    @contextmanager
    def suite(self, headline, *args):
        self.stmt(headline, *args)
        prev = self._curr
        self._curr = []
        prev.append(self._curr)
        yield
        self._curr = prev
    @contextmanager
    def if_(self, cond, *args):
        with self.suite("if %s:" % (cond,), *args): yield
    @contextmanager
    def elif_(self, cond, *args):
        with self.suite("elif %s:" % (cond,), *args): yield
    @contextmanager
    def else_(self):
        with self.suite("else:"): yield
    @contextmanager
    def for_(self, var, expr):
        with self.suite("for %s in %s:" % (var, expr)): yield
    @contextmanager
    def while_(self, cond, *args):
        with self.suite("while %s:" % (cond,), *args): yield
    @contextmanager
    def try_(self):
        with self.suite("try:"): yield
    @contextmanager
    def except_(self, exceptions, var = None):
        if var:
            with self.suite("except (%s) as %s:" % (", ".join(exceptions), var)): yield
        else:
            with self.suite("except (%s):" % (", ".join(exceptions),)): yield
    @contextmanager
    def finally_(self):
        with self.suite("finally:"): yield
    @contextmanager
    def def_(self, name, *args):
        with self.suite("def %s(%s):" % (name, ", ".join(str(a) for a in args))): yield
        self.sep()
    @contextmanager
    def class_(self, name, bases = ("object",)):
        with self.suite("class %s(%s):" % (name, ", ".join(bases,))): yield
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

class P(object):
    """
    Pickled object
    """
    __slots__ = ["data"]
    def __init__(self, obj):
        self.data = "pickle.loads(%r)" % (pickle.dumps(obj),)
    def __str__(self):
        return self.data
    __repr__ = __str__

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
    def __floordiv__(self, other):
        return E("(%r // %r)" % (self, other))
    def __mod__(self, other):
        return E("(%r % %r)" % (self, other))
    def __pow__(self, other):
        return E("(%r % %r)" % (self, other))
    def __or__(self, other):
        return E("(%r or %r)" % (self, other))
    def __and__(self, other):
        return E("(%r and %r)" % (self, other))
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
    def __rfloordiv__(self, other):
        return E("(%r // %r)" % (other, self))
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
        return E("not %r" % (self,))
    __invert__ = __inv__
    
    def __getitem__(self, key):
        return E("%r[%r]" % (self, key))
    def __getattr__(self, name):
        return E("%r.%s" % (self, name))
    def __call__(self, *args, **kwargs):
        textargs = ""
        if args:
            textargs += ", ".join(repr(a) for a in args)
        if kwargs:
            if args:
                textargs += ", "
            textargs += ",".join("%s = %r" % (k, v) for k, v in kwargs.items())
        return E("%r(%s)" % (self, textargs))


#if __name__ == "__main__":
#    m = PythonModule("foo")
#    m.import_("sys")
#    m.import_("pickle")
#    m.sep()
#    with m.if_("x > {0}", P(7)):
#        m.stmt("print {0}", R("oh no"))
#        m.stmt(R(z = P(10)))
#    m.stmt(E("foo")[3].bar(122, z = 8))
#    m.stmt(R(w = E(17) - 6))
#    
#    print m
#

