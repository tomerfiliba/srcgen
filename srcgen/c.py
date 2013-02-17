from __future__ import with_statement
from srcgen.base import BaseModule, BaseE, R
from contextlib import contextmanager


class CModule(BaseModule):
    def comment(self, *lines, **kwargs):
        box = kwargs.pop("box", False)
        sep = kwargs.pop("sep", False)
        if sep and box:
            self._curr.append("")
            self._curr.append("/* " + "*" * (self._line_width-2))
        elif sep:
            self._curr.append("/*")
        elif box:
            self._curr.append("/* " + "*" * (self._line_width-2))
        self._curr.extend("/* %s" % (l.replace("*/", "* /"),) for l in "\n".join(lines).splitlines())
        if sep and box:
            self._curr.append("*" * (self._line_width - 2) + " */")
            self._curr.append("")
        elif sep:
            self._curr.append("*/")
        elif box:
            self._curr.append("*" * (self._line_width - 2) + " */")
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
        filename = str(filename)
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
        if terminator is None:
            self._curr.append("}")
        else:
            if terminator:
                self._curr.append(terminator)

    def if_(self, cond, *args):
        return self.suite("if (%s)" % (cond,), *args)
    def elif_(self, cond, *args):
        return self.suite("else if (%s)" % (cond,), *args)
    def else_(self):
        return self.suite("else")
    def for_(self, init, cond, next):
        return self.suite("for (%s; %s; %s)" % (init, cond, next))
    def while_(self, cond, *args):
        return self.suite("while %s:" % (cond,), *args)
    def do_while(self, cond, *args):
        return self.suite("do", terminator = "} while(%s);" % (cond,), *args)

    def switch(self, cond, *args):
        return self.suite("switch (%s)" % (cond,),  *args)
    def case(self, val, *args):
        return self.suite("case %s:" % (val,), terminator = "", *args)
    def default(self):
        return self.suite("default:", terminator = "")
    
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

    # preprocessor stuff
    @contextmanager
    def _if_suite(self, headline, merge_endif):
        if merge_endif and self._curr and self._curr[-1].startswith("#endif"):
            self._curr.pop(-1)
        self._curr.append(headline)
        prev = self._curr
        self._curr = []
        prev.append(self._curr)
        yield
        self._curr = prev
        self.stmt("#endif")
    
    def IF(self, cond):
        return self._if_suite("#if %s" % (cond,), False)
    def ELIF(self, cond):
        return self._if_suite("#elif %s" % (cond,), True)
    def ELSE(self, cond):
        return self._if_suite("#else %s" % (cond,), True)
    def IFDEF(self, name):
        return self._if_suite("#ifdef %s" % (name,), False)
    def IFNDEF(self, name):
        return self._if_suite("#ifndef %s" % (name,), False)

class HModule(CModule):
    def __init__(self, guard_name):
        CModule.__init__(self)
        self._guard_name = guard_name
    def render(self):
        text = CModule.render(self)
        text = "#ifndef %s\n#define %s\n\n" % (self._guard_name, self._guard_name) + text
        text += "\n#endif /* %s */\n" % (self._guard_name,)
        return text


class E(BaseE):
    def __call__(self, *args):
        return E("%r(%s)" % (self, ", ".join(repr(a) for a in args)))






