from __future__ import with_statement
from threading import local


_per_thread = local()

class PythonModule(object):
    __slos__ = ["name", "children"]
    def __init__(self, name):
        self.name = name
        self.children = []
    def __enter__(self):
        _per_thread.stack = [self]
        return self
    def __exit__(self, t, v, tb):
        del _per_thread.stack
    def __repr__(self):
        return "PythonModule(%r, %d children)" % (self.name, len(self.children))
    def __str__(self):
        return self.render()
    
    def render(self):
        """Returns a textual representation of the module (string)"""
        return "\n".join("\n".join(child._render(0)) for child in self.children)
    def dump(self, file):
        """Renders the module and dumps it to the given file. ``file`` can be either a file name or 
        a file object"""
        data = self.render()
        if hasattr(file, "write"):
            file.write(data)
        else:
            with open(file, "w") as f:
                f.write(data)

class Node(object):
    __slos__ = []
    def __init__(self):
        _per_thread.stack[-1].children.append(self)
    def _render(self, level):
        raise NotImplementedError()

#=======================================================================================================================
# Suites
#=======================================================================================================================
class Suite(Node):
    __slos__ = ["headline", "children"]
    ADD_SEP = False
    def __init__(self, headline):
        Node.__init__(self)
        self.headline = headline
        self.children = []
    def __enter__(self,):
        _per_thread.stack.append(self)
        return self
    def __exit__(self, t, v, tb):
        _per_thread.stack.pop(-1)
    def __repr__(self):
        return "%s(%r, %d children)" % (self.__class__.__name__, self.headline, len(self.children))
    def _render(self, level):
        yield "    " * level + self.headline + ":"
        if not self.children:
            yield "    " * (level + 1) + "pass"
        else:
            for child in self.children:
                for line in child._render(level + 1):
                    yield line
        if self.ADD_SEP:
            yield ""

class IF(Suite):
    __slots__ = []
    def __init__(self, cond):
        Suite.__init__(self, "if %s" % (cond,))

class ELIF(Suite):
    __slots__ = []
    def __init__(self, cond):
        Suite.__init__(self, "elif %s" % (cond,))

class ELSE(Suite):
    __slots__ = []
    def __init__(self):
        Suite.__init__(self, "else")

class TRY(Suite):
    __slots__ = []
    def __init__(self):
        Suite.__init__(self, "try")

class EXCEPT(Suite):
    __slots__ = []
    def __init__(self, exceptions, varname = None):
        if varname:
            Suite.__init__(self, "except (%s)" % (", ".join(exceptions),))
        else:
            Suite.__init__(self, "except (%s) as %s" % (", ".join(exceptions), varname))

class FINALLY(Suite):
    __slots__ = []
    def __init__(self):
        Suite.__init__(self, "finally")

class WHILE(Suite):
    __slots__ = []
    def __init__(self, cond):
        Suite.__init__(self, "while %s" % (cond,))

class FOR(Suite):
    __slots__ = []
    def __init__(self, var, iterable):
        Suite.__init__(self, "for %s in %s" % (var, iterable))

class WITH(Suite):
    __slots__ = []
    def __init__(self, *exprs):
        Suite.__init__(self, "with %s" % (", ".join(exprs),))

class CLASS(Suite):
    __slots__ = []
    ADD_SEP = True
    def __init__(self, name, bases = (object,)):
        Suite.__init__(self, "class %s(%s)" % (name, ", ".join(bases)))

class DEF(Suite):
    __slots__ = []
    ADD_SEP = True
    def __init__(self, name, args = ()):
        Suite.__init__(self, "def %s(%s)" % (name, ", ".join(args)))

#=======================================================================================================================
# Statements
#=======================================================================================================================
class SEP(Node):
    __slots__ = ["count"]
    def __init__(self, count = 1):
        Node.__init__(self)
        self.count = count
    def __repr__(self):
        return "SEP(%r)" % (self.count,)
    def _render(self, level):
        for _ in range(self.count):
            yield ""

class COMMENT(Node):
    __slots__ = ["lines", "box", "sep"]
    LINE_WIDTH = 80
    def __init__(self, *lines, **kwargs):
        Node.__init__(self)
        self.box = kwargs.pop("box", False)
        self.sep = kwargs.pop("sep", False)
        if kwargs:
            raise TypeError("Unknown keyword arguments %r" % (kwargs.keys(),))
        self.lines = "\n".join(lines).splitlines()
    def __repr__(self):
        return "COMMENT(%s)" % (", ".join(repr(l) for l in self.lines))
    def _render(self, level):
        indent = "    " * level
        if self.sep:
            yield ""
        if self.box:
            yield indent + "#" * (self.LINE_WIDTH - level * 4)
        for line in self.lines:
            yield indent + "# " + line
        if self.box:
            yield indent + "#" * (self.LINE_WIDTH - level * 4)
        if self.sep:
            yield ""

class STMT(Node):
    __slots__ = ["text"]
    def __init__(self, fmt, *args):
        Node.__init__(self)
        self.text = fmt.format(*args) if args else fmt
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.text)
    def _render(self, level):
        yield "    " * level + self.text

class IMPORT(STMT):
    __slots__ = []
    def __init__(self, *modnames):
        STMT.__init__(self, "import %s" % (", ".join(modnames),))

class FROM_IMPORT(STMT):
    __slots__ = []
    def __init__(self, modname, *attrs):
        STMT.__init__(self, "from %s import %s" % (modname, ", ".join(attrs)))

class RETURN(STMT):
    __slots__ = []
    def __init__(self, expr):
        STMT.__init__(self, "return %s" % (expr,))

class YIELD(STMT):
    __slots__ = []
    def __init__(self, expr):
        STMT.__init__(self, "yield %s" % (expr,))

class RAISE(STMT):
    __slots__ = []
    def __init__(self, expr):
        STMT.__init__(self, "raise %s" % (expr,))

class BREAK(STMT):
    __slots__ = []
    def __init__(self):
        STMT.__init__(self, "break")

class CONTINUE(STMT):
    __slots__ = []
    def __init__(self):
        STMT.__init__(self, "continue")


