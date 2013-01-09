import threading
import six
import sys


class Unescaped(str):
    __slots__ = ()
    def __repr__(self):
        return "Unescaped(%s)" % (str.__repr__(self))
    def __add__(self, other):
        return Unescaped(str.__add__(self, xml_escape(other)))
    def __radd__(self, other):
        return Unescaped(str.__add__(xml_escape(other), self))
    def __mod__(self, arg):
        if isinstance(arg, tuple):
            return Unescaped(str.__mod__(self, tuple(xml_escape(a) if isinstance(a, str) else a for a in arg)))
        elif isinstance(arg, dict):
            return Unescaped(str.__mod__(self, dict((k, (xml_escape(v) if isinstance(v, str) else v)) 
                for k, v in arg.items())))
        elif isinstance(arg, str): 
            return Unescaped(str.__mod__(self, xml_escape(arg)))
        else:
            return Unescaped(str.__mod__(self, arg))
    def format(self, *args, **kwargs):
        pass
    def join(self, iterable):
        return Unescaped(str.join(self, (xml_escape(e) if isinstance(e, str) else e for e in iterable)))
    
    for name in ['__format__', '__mul__', '__rmul__', 'capitalize', 'center', 'expandtabs', 'format', 'ljust', 
                'lower', 'lstrip', 'rjust', 'rstrip', 'strip', 'swapcase', 'title', 'translate', 'upper', 'zfill']:
        if name not in str.__dict__:
            continue
        def mkmethod(name):
            def method(*args, **kwargs):
                return Unescaped(getattr(str, name)(*args, **kwargs))
            method.__name__ = name
            method.__doc__ = getattr(str, name).__doc__
            return method
        locals()[name] = mkmethod(name)
    del mkmethod, name

_MAPPING = {"&" : "&amp;", "'" : "&apos;", '"' : "&quot;", "<" : "&lt;", ">" : "&gt;"}

def xml_escape(text):
    if isinstance(text, Unescaped):
        return str(text)
    else:
        return "".join(_MAPPING.get(ch, ch) for ch in str(text))

_per_thread = threading.local()

class ElementMetaclass(type):
    __slots__ = ()
    def __getattr__(self, name):
        return self(class_ = name)
    def __enter__(self):
        return self().__enter__()
    def __exit__(self, t, v, tb):
        _per_thread.stack[-1].__exit__(t, v, tb)

# hack for python < 2.6, as __enter__ and __exit__ were not real slots back then
# (they are not looked up in the metaclass) {{
class Enterer(object):
    __slots__ = ["func"]
    def __init__(self, func):
        self.func = func
    def __get__(self, inst, cls):
        if inst is None:
            inst = cls()
        return self.func.__get__(inst, cls)

class Exiter(object):
    __slots__ = ["func"]
    def __init__(self, func):
        self.func = func
    def __get__(self, inst, cls):
        if inst is None:
            if _per_thread.stack:
                return _per_thread.stack[-1].__exit__
            else:
                return lambda *a: None
        return self.func.__get__(inst, cls)
# }}

class Element(six.with_metaclass(ElementMetaclass)):
    __slots__ = ["_attrs", "_elems", "_parent"]
    TAG = None
    DEFAULT_ATTRS = {}
    INLINE = False
    
    def __init__(self, *elems, **attrs):
        self._elems = []
        self._attrs = self.DEFAULT_ATTRS.copy()
        if getattr(_per_thread, "stack", None):
            self._parent = _per_thread.stack[-1]
            self._parent._elems.append(self)
        else:
            self._parent = None
        self(*elems, **attrs)

    def __repr__(self):
        return "<Element %s(%s), %s subelements>" % (self.__class__.__name__,
            ", ".join("%s=%r" % (k, v) for k, v in self._attrs.items()), len(self._elems))
    def __str__(self):
        return self._render(0, False)
    
    def __enter__(self):
        if not hasattr(_per_thread, "stack"):
            _per_thread.stack = []
        _per_thread.stack.append(self)
        return self
    def __exit__(self, t, v, tb):
        _per_thread.stack.pop(-1)
    
    # python <= 2.6.x hacks {{
    if sys.version_info < (2, 7):
        __enter__ = Enterer(__enter__)
        __exit__ = Exiter(__exit__)
    # }}

    def __getitem__(self, name):
        return self._attrs[name]
    def __delitem__(self, name):
        del self._attrs[name]
    def __setitem__(self, name, value):
        self._attrs[name] = value
    
    def __call__(self, *elems, **attrs):
        for elem in elems:
            if isinstance(elem, Element):
                if elem._parent is not None:
                    elem._parent._elems.remove(elem)
                elem._parent = self
            self._elems.append(elem)
        for k, v in attrs.items():
            if k.endswith("_"):
                k = k[:-1]
            self._attrs[k.replace("_", "-")] = v
        return self
    
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if "class" in self._attrs:
            self._attrs["class"] += " " + name
        else:
            self._attrs["class"] = name
        return self
    
    def _render(self, level, compact):
        indent = "" if compact else "  " * level
        tag = self.TAG if self.TAG else self.__class__.__name__.lower().rstrip("_")
        attrs = " ".join('%s="%s"' % (k, xml_escape(str(v))) for k, v in sorted(self._attrs.items()))
        if attrs:
            attrs = " " + attrs
        if self._elems:
            elements = "\n".join(e._render(level + 1, compact) if isinstance(e, Element) else xml_escape(e) 
                for e in self._elems)
            
            if self.INLINE or not "\n" in elements:
                elements = " ".join(e._render(level + 1, True) if isinstance(e, Element) else xml_escape(e) 
                    for e in self._elems)
                result = "<%s%s>%s</%s>" % (tag, attrs, elements, tag)
            else:
                result = "<%s%s>\n%s\n%s</%s>" % (tag, attrs, elements, indent, tag)
        else:
            result = "<%s%s/>" % (tag, attrs)
        return indent + result

def THIS():
    return _per_thread.stack[-1]
def PARENT(count = 1):
    return _per_thread.stack[-1 - count]
def TEXT(*texts):
    THIS()(*texts)
def UNESCAPED(*texts):
    THIS()(*(Unescaped(text) for text in texts))
def EMBED(element):
    THIS()(element)
def ATTR(**kwargs):
    THIS()(**kwargs)

class COMMENT(Element):
    def _render(self, level, compact):
        indent = "" if compact else "  " * level
        elements = "\n".join(e._render(level + 1, compact) if isinstance(e, Element) else xml_escape(e) 
                for e in self._elems)
        if "\n" not in elements:
            return "%s<!-- %s -->" % (indent, elements.replace("-->", "-- >"))
        else:
            return "%s<!--\n%s\n%s-->" % (indent, elements.replace("-->", "-- >"), indent)

class html(Element):
    DEFAULT_ATTRS = {"xmlns" : "http://www.w3.org/1999/xhtml"}
    DOCTYPE = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
    
    def _render(self, level, compact):
        text = Element._render(self, level, compact)
        if self.DOCTYPE:
            text = self.DOCTYPE + "\n" + text
        return text

class head(Element): pass
class body(Element): pass
class link(Element): INLINE = True
class meta(Element): INLINE = True
class title(Element): INLINE = True

class script(Element): DEFAULT_ATTRS = {"type" : "text/javascript"}
class style(Element): DEFAULT_ATTRS = {"type" : "text/css"}

class p(Element): pass
class div(Element): pass
class blockquote(Element): pass

class dl(Element): pass
class dt(Element): pass
class dd(Element): pass
class li(Element): pass
class ul(Element): pass
class ol(Element): pass

class form(Element): pass
class input(Element): pass
class button(Element): pass
class select(Element): pass
class label(Element): pass
class optgroup(Element): pass
class option(Element): pass
class textarea(Element): pass
class legend(Element): pass

class table(Element): pass
class tr(Element): pass
class th(Element): pass
class td(Element): pass
class colgroup(Element): pass
class thead(Element): pass
class tbody(Element): pass
class tfoot(Element): pass

class frame(Element): pass
class iframe(Element): pass
class noframe(Element): pass
class frameset(Element): pass

class img(Element): INLINE = True

class pre(Element): INLINE = True
class code(Element): INLINE = True
class span(Element): INLINE = True
class a(Element): INLINE = True
class br(Element): INLINE = True
class hr(Element): INLINE = True
class em(Element): INLINE = True
class strong(Element): INLINE = True
class cite(Element): INLINE = True
class i(Element): INLINE = True
class b(Element): INLINE = True
class u(Element): INLINE = True
class sub(Element): INLINE = True
class sup(Element): INLINE = True
class big(Element): INLINE = True
class small(Element): INLINE = True

class h1(Element): INLINE = True
class h2(Element): INLINE = True
class h3(Element): INLINE = True
class h4(Element): INLINE = True
class h5(Element): INLINE = True
class h6(Element): INLINE = True

__all__ = ["TEXT", "COMMENT", "Unescaped", "UNESCAPED", "ATTR", "EMBED", "THIS", "PARENT"]
__all__.extend(cls.__name__ for cls in Element.__subclasses__())

