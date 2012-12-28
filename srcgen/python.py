from __future__ import with_statement
from threading import local


_per_thread = local()

class PythonModule(object):
    def __init__(self, name):
        self.name = name
        self.children = []
    def __enter__(self):
        _per_thread.stack = [self]
        return self
    def __exit__(self, t, v, tb):
        del _per_thread.stack
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
    def __init__(self):
        _per_thread.stack[-1].children.append(self)

#=======================================================================================================================
# Suites
#=======================================================================================================================
class Suite(Node):
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
    def __init__(self, cond):
        self.cond = cond
        Suite.__init__(self, "if %s" % (cond,))
class ELIF(Suite):
    def __init__(self, cond):
        self.cond = cond
        Suite.__init__(self, "elif %s" % (cond,))
class ELSE(Suite):
    def __init__(self):
        Suite.__init__(self, "else")
class TRY(Suite):
    def __init__(self):
        Suite.__init__(self, "else")
class EXCEPT(Suite):
    def __init__(self, exceptions, varname = None):
        self.exceptions = exceptions
        self.varname = varname
        if varname:
            Suite.__init__(self, "except (%s)" % (", ".join(exceptions),))
        else:
            Suite.__init__(self, "except (%s) as %s" % (", ".join(exceptions), varname))
class FINALLY(Suite):
    def __init__(self):
        Suite.__init__(self, "finally")
class WHILE(Suite):
    def __init__(self, cond):
        self.cond = cond
        Suite.__init__(self, "while %s" % (cond,))
class FOR(Suite):
    def __init__(self, var, iterable):
        self.var = var
        self.iterable = iterable
        Suite.__init__(self, "for %s in %s" % (var, iterable))
class WITH(Suite):
    def __init__(self, *exprs):
        self.exprs = exprs
        Suite.__init__(self, "with %s" % (", ".join(exprs),))
class CLASS(Suite):
    ADD_SEP = True
    def __init__(self, name, bases = (object,)):
        self.name = name
        self.bases = bases
        Suite.__init__(self, "class %s(%s)" % (name, ", ".join(bases)))
class DEF(Suite):
    ADD_SEP = True
    def __init__(self, name, args = ()):
        self.name = name
        self.args = args
        Suite.__init__(self, "def %s(%s)" % (name, ", ".join(args)))

#=======================================================================================================================
# Statements
#=======================================================================================================================
class SEP(Node):
    def __init__(self, count = 1):
        Node.__init__(self)
        self.count = count
    def _render(self, level):
        for _ in range(self.count):
            yield ""

class DOC(Node):
    LINE_WIDTH = 80
    def __init__(self, *lines, **kwargs):
        Node.__init__(self)
        self.box = kwargs.pop("box", False)
        self.sep = kwargs.pop("sep", False)
        if kwargs:
            raise TypeError("Unknown keyword arguments %r" % (kwargs.keys(),))
        self.lines = "\n".join(lines).splitlines()
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
    def __init__(self, fmt, *args):
        Node.__init__(self)
        self.text = fmt.format(*args) if args else fmt
    def _render(self, level):
        yield "    " * level + self.text
class IMPORT(STMT):
    def __init__(self, *modnames):
        STMT.__init__(self, "import %s" % (", ".join(modnames),))
class FROM_IMPORT(STMT):
    def __init__(self, modname, *attrs):
        STMT.__init__(self, "from %s import %s" % (modname, ", ".join(attrs)))
class RETURN(STMT):
    def __init__(self, expr):
        STMT.__init__(self, "return %s" % (expr,))
class YIELD(STMT):
    def __init__(self, expr):
        STMT.__init__(self, "yield %s" % (expr,))
class RAISE(STMT):
    def __init__(self, expr):
        STMT.__init__(self, "raise %s" % (expr,))
class BREAK(STMT):
    def __init__(self):
        STMT.__init__(self, "break")
class CONTINUE(STMT):
    def __init__(self):
        STMT.__init__(self, "continue")



