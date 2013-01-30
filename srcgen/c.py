from __future__ import with_statement
from srcgen.base import BaseModule, BaseE, R
from contextlib import contextmanager


class CModule(BaseModule):
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


class E(BaseE):
    def __call__(self, *args):
        return E("%r(%s)" % (self, ", ".join(repr(a) for a in args)))






