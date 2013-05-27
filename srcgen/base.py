class BaseModule(object):
    def __init__(self, name = None, line_width = 80, indentation = "    "):
        self._indentation = indentation
        self._name = name
        self._line_width = line_width
        self._curr = []
        self._sep_lines = 0
    def __str__(self):
        return self.render()
    
    @classmethod
    def _render(cls, curr, level, indentation):
        indent = indentation * level
        for elem in curr:
            if isinstance(elem, list):
                for line in cls._render(elem, level + 1, indentation):
                    yield line
            else:
                line = str(elem)
                yield indent + line if line.strip() else ""
    def render(self):
        text = "\n".join(self._render(self._curr, 0, self._indentation))
        if not text.endswith("\n"):
            text += "\n"
        return text
        
    def dump(self, filename_or_fileobj):
        """Renders the module and dumps it to the given file. ``file`` can be either a file name or 
        a file object"""
        data = self.render()
        if hasattr(filename_or_fileobj, "write"):
            filename_or_fileobj.write(data)
        else:
            with open(filename_or_fileobj, "w") as f:
                f.write(data)

    def sep(self, count = 1):
        if self._sep_lines >= count:
            return
        self._curr.extend("" for _ in range(count))
        self._sep_lines += count
    
    def _append(self, line):
        if line.strip():
            self._curr.append(line)
            self._sep_lines = 0
        else:
            self._curr.append("")
            self._sep_lines += 1

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


class BaseE(object):
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
        return self.__class__("(%r + %r)" % (self, other))
    def __sub__(self, other):
        return self.__class__("(%r - %r)" % (self, other))
    def __mul__(self, other):
        return self.__class__("(%r * %r)" % (self, other))
    def __truediv__(self, other):
        return self.__class__("(%r / %r)" % (self, other))
    __div__ = __truediv__
    def __mod__(self, other):
        return self.__class__("(%r % %r)" % (self, other))
    def __pow__(self, other):
        return self.__class__("(%r % %r)" % (self, other))
    def __or__(self, other):
        return self.__class__("(%r | %r)" % (self, other))
    def __and__(self, other):
        return self.__class__("(%r & %r)" % (self, other))
    def __xor__(self, other):
        return self.__class__("(%r ^ %r)" % (self, other))
    def __lshift__(self, other):
        return self.__class__("(%r << %r)" % (self, other))
    def __rshift__(self, other):
        return self.__class__("(%r >> %r)" % (self, other))

    def __radd__(self, other):
        return self.__class__("(%r + %r)" % (other, self))
    def __rsub__(self, other):
        return self.__class__("(%r - %r)" % (other, self))
    def __rmul__(self, other):
        return self.__class__("(%r * %r)" % (other, self))
    def __rtruediv__(self, other):
        return self.__class__("(%r / %r)" % (other, self))
    __rdiv__ = __rtruediv__
    def __rmod__(self, other):
        return self.__class__("(%r % %r)" % (other, self))
    def __rpow__(self, other):
        return self.__class__("(%r % %r)" % (other, self))
    def __ror__(self, other):
        return self.__class__("(%r or %r)" % (other, self))
    def __rand__(self, other):
        return self.__class__("(%r and %r)" % (other, self))
    def __rxor__(self, other):
        return self.__class__("(%r ^ %r)" % (other, self))
    def __rlshift__(self, other):
        return self.__class__("(%r << %r)" % (other, self))
    def __rrshift__(self, other):
        return self.__class__("(%r >> %r)" % (other, self))
    
    def __gt__(self, other):
        return self.__class__("(%r > %r)" % (self, other))
    def __ge__(self, other):
        return self.__class__("(%r >= %r)" % (self, other))
    def __lt__(self, other):
        return self.__class__("(%r < %r)" % (self, other))
    def __le__(self, other):
        return self.__class__("(%r <= %r)" % (self, other))
    def __eq__(self, other):
        return self.__class__("(%r == %r)" % (self, other))
    def __ne__(self, other):
        return self.__class__("(%r != %r)" % (self, other))
    
    def __neg__(self):
        return self.__class__("-%r" % (self,))
    def __pos__(self):
        return self.__class__("+%r" % (self,))
    def __inv__(self):
        return self.__class__("~%r" % (self,))
    __invert__ = __inv__
    
    def __getitem__(self, key):
        return self.__class__("%r[%r]" % (self, key))
    def __getattr__(self, name):
        return self.__class__("%r.%s" % (self, name))



