import json
from srcgen.base import BaseModule
from contextlib import contextmanager
from srcgen.html import Htmlable, xml_escape


class JS(BaseModule, Htmlable):
    def comment(self, *lines, **kwargs):
        box = kwargs.pop("box", False)
        sep = kwargs.pop("sep", False)
        if sep and box:
            self._append("")
            self._append("/* " + "*" * (self._line_width-2))
        elif sep:
            self._append("/*")
        elif box:
            self._append("/* " + "*" * (self._line_width-2))
        self._curr.extend("/* %s" % (l.replace("*/", "* /"),) for l in "\n".join(lines).splitlines())
        if sep and box:
            self._append("*" * (self._line_width - 2) + " */")
            self._append("")
        elif sep:
            self._append("*/")
        elif box:
            self._append("*" * (self._line_width - 2) + " */")
        else:
            self._curr[-1] += " */"
    
    def render_html(self):
        for line in xml_escape(self.render()).splitlines():
            yield 0, True, line
    
    def stmt(self, text, *args, **kwargs):
        text = str(text)
        semicolon = kwargs.pop("semicolon", True)
        if kwargs:
            raise TypeError("Invalid keyword argument %r" % (kwargs.keys(),))
        if semicolon and text.strip()[0] != "#" and text[-1] not in ";:,{":
            text += ";"
        self._append(text.format(*args) if args else text)
    def break_(self):
        self.stmt("break")
    def continue_(self):
        self.stmt("continue")
    def return_(self, expr, *args):
        self.stmt("return %s" % (expr,), *args)
    def var(self, name, init = None):
        self.stmt("var {0} = {1}", name, init if isinstance(init, str) else json.dumps(init))
    
    @contextmanager
    def suite(self, headline, *args, **kwargs):
        headline = str(headline)
        terminator = kwargs.pop("terminator", None)
        if kwargs:
            raise TypeError("Invalid keyword argument %r" % (kwargs.keys(),))
        if headline[-1] not in "{:":
            headline += " {"
        self._append(headline.format(*args) if args else headline)
        prev = self._curr
        self._curr = []
        prev.append(self._curr)
        yield
        self._curr = prev
        if terminator is None:
            self._append("}")
        else:
            if terminator:
                self._append(terminator)

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

    @contextmanager
    def func(self, name, *args):
        with self.suite("function %s(%s)" % (name, ", ".join(str(a) for a in args))): yield
        self.sep()


class JExpr(object):
    __slots__ = ["_text"]
    def __init__(self, text):
        object.__setattr__(self, "_text", text)
    def __str__(self):
        return self._text
    def __getattr__(self, name):
        return JExpr("%s.%s" % (self, name))
    def __setattr__(self, name, value):
        return JExpr("%s.%s = %s" % (self, name, value if isinstance(value, str) else json.dumps(value)))
    def __getitem__(self, index):
        return JExpr("%s[%s]" % (self, json.dumps(index)))
    def __setitem__(self, index, val):
        return JExpr("%s[%s] = %s" % (self, json.dumps(index), val if isinstance(val, str) else json.dumps(val)))
    def __call__(self, *args):
        return JExpr("%s(%s)" % (self, ", ".join(json.dumps(a) for a in args)))
    def __add__(self, other):
        return JExpr("(%s + %s)" % (self, other))
    def __sub__(self, other):
        return JExpr("(%s - %s)" % (self, other))
    def __mul__(self, other):
        return JExpr("(%s * %s)" % (self, other))
    def __div__(self, other):
        return JExpr("(%s / %s)" % (self, other))
    def __pow__(self, other):
        return JExpr("(%s ** %s)" % (self, other))
    
#    @contextmanager
#    def func(self, *args):
#        body = JS()
#        yield body
#        return JExp("%s(function(%s) {\n%s\n})" % (", ".join(json.dumps(a) for a in args), body))


#if __name__ == "__main__":
#    m = JS()
#    with m.func("foo", "a", "b"):
#        with m.if_("a > b"):
#            m.return_(17)
#        with m.else_():
#            m.return_(18)
#    
#    print m
    






