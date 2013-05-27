from __future__ import with_statement
import pickle
import six
from contextlib import contextmanager
from srcgen.base import BaseModule, BaseE, R


class PythonModule(BaseModule):
    def comment(self, *lines, **kwargs):
        box = kwargs.pop("box", False)
        sep = kwargs.pop("sep", False)
        if sep and box:
            self._append("")
            self._append("#" * self._line_width)
        elif sep:
            self._append("#")
        elif box:
            self._append("#" * self._line_width)
        self._curr.extend("# %s" % (l,) for l in "\n".join(lines).splitlines())
        if sep and box:
            self._append("#" * self._line_width)
            self._append("")
        elif sep:
            self._append("#")
        elif box:
            self._append("#" * self._line_width)    
    
    #
    # Statements
    #
    def stmt(self, text, *args):
        self._append(text.format(*args) if args else text)
    def doc(self, text):
        self.stmt(repr(text))
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
    def pass_(self):
        self.stmt("pass")
    
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
        if isinstance(bases, six.string_types):
            bases = (bases,)
        with self.suite("class %s(%s):" % (name, ", ".join(bases,))): yield
        self.sep()

    @contextmanager
    def cython(self):
        mod = CythonModule()
        mod._curr = self._curr
        yield mod

    def method(self, name, *args):
        args = ("self",) + args
        return self.def_(name, *args)
    def classmethod(self, name, *args):
        args = ("cls",) + args
        self.stmt("@classmethod")
        return self.def_(name, *args)
    def staticmethod(self, name, *args):
        self.stmt("@staticmethod")
        return self.def_(name, *args)


class CythonModule(PythonModule):
    def __init__(self, *args, **kwargs):
        PythonModule.__init__(self, *args, **kwargs)
        self._in_cdef = False
        
    @property
    def cdef(self):
        self._in_cdef = True
        return self
    
    @contextmanager
    def __call__(self, name, *args):
        assert self._in_cdef
        with self.suite("%s(%s):" % (name, ", ".join(str(a) for a in args))): yield
        self.sep()
    
    def stmt(self, text, *args):
        in_cdef = self._in_cdef
        self._in_cdef = False
        PythonModule.stmt(self, ("cdef " + text) if in_cdef else text, *args)
    
    def typedef(self, type, newname):
        self.stmt("ctypedef %s %s" % (type, newname))
    
    @contextmanager
    def suite(self, text, *args):
        in_cdef = self._in_cdef
        self._in_cdef = False
        with PythonModule.suite(self, ("cdef " + text) if in_cdef else text, *args): yield
    
    def cppclass(self, name, bases = ()):
        return self.suite("cppclass %s:" % (name))
    
    @contextmanager
    def extern(self, from_ = None, namespace = None):
        head = "extern"
        if from_:
            head += ' from "%s"' % (repr(from_)[1:-1],)
        if namespace:
            head += ' namespace "%s"' % (repr(namespace)[1:-1],)
        with self.suite(head): yield
        self.sep()
    
    @contextmanager
    def struct(self, name):
        with self.suite("struct %s:" % (name,)): yield
        self.sep()
    @contextmanager
    def union(self, name):
        with self.suite("union %s:" % (name,)): yield
        self.sep()
    @contextmanager
    def enum(self, name):
        with self.suite("enum %s:" % (name,)): yield
        self.sep()

    @contextmanager
    def property(self, name):
        with self.suite("property %s:" % (name,)): yield
        self.sep()
    @contextmanager
    def get(self):
        with self.suite("def __get__(self):"): yield
        self.sep()
    @contextmanager
    def set(self):
        with self.suite("def __set__(self, value):"): yield
        self.sep()
    @contextmanager
    def get_property(self, name):
        with self.property(name):
            with self.get():
                yield


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

class E(BaseE):
    __slots__ = []
    
    def __floordiv__(self, other):
        return E("(%r // %r)" % (self, other))
    def __or__(self, other):
        return E("(%r or %r)" % (self, other))
    def __and__(self, other):
        return E("(%r and %r)" % (self, other))
    def __rfloordiv__(self, other):
        return E("(%r // %r)" % (other, self))
    def __ror__(self, other):
        return E("(%r or %r)" % (other, self))
    def __rand__(self, other):
        return E("(%r and %r)" % (other, self))
    
    def __inv__(self):
        return E("not %r" % (self,))
    __invert__ = __inv__
    
    def __call__(self, *args, **kwargs):
        textargs = ""
        if args:
            textargs += ", ".join(repr(a) for a in args)
        if kwargs:
            if args:
                textargs += ", "
            textargs += ",".join("%s = %r" % (k, v) for k, v in kwargs.items())
        return E("%r(%s)" % (self, textargs))


