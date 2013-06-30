import weakref
import six
import itertools
from contextlib import contextmanager
from functools import partial


_MAPPING = {"&" : "&amp;", "'" : "&apos;", '"' : "&quot;", "<" : "&lt;", ">" : "&gt;"}
def xml_escape(text):
    if text is None:
        return ""
    return "".join(_MAPPING.get(ch, ch) for ch in str(text))

class Htmlable(object):
    __slots__ = []
    
    def render_html(self):
        raise NotImplementedError()

class HtmlElement(Htmlable):
    __slots__ = ["doc", "tag", "attrs", "elements"]
    MULTILINE = True
    
    def __init__(self, doc, tag, elems, attrs):
        self.doc = doc
        self.tag = tag
        self.attrs = attrs
        self.elements = elems
    
    def __enter__(self):
        self.doc._push(self)
        return self
    def __exit__(self, t, v, tb):
        self.doc._pop()
    
    def _format_attrs(self):
        attrs = []
        for k, v in self.attrs.items():
            if k.startswith("_") or v is None or v is False:
                continue
            k = k.rstrip("_").replace("_", "-")
            if v is True:
                attrs.append(xml_escape(k))
            else:
                attrs.append('%s="%s"' % (xml_escape(k), xml_escape(v)))
        if attrs:
            attrs = " " + " ".join(attrs)
        else:
            attrs = ""
        return attrs
        
    def render_html(self):
        attrs = self._format_attrs()
        if self.elements:
            yield 0, self.MULTILINE, "<%s%s>" % (xml_escape(self.tag), attrs)
            for elem in self.elements:
                if elem is None:
                    continue
                if isinstance(elem, Htmlable):
                    for level, nl, line in elem.render_html():
                        yield level + 1, nl, line
                else:
                    yield 1, False, xml_escape(elem)
            yield 0, self.MULTILINE, "</%s>" % (xml_escape(self.tag),)
        else:
            yield 0, self.MULTILINE, "<%s%s/>" % (xml_escape(self.tag), attrs)

class InlineHtmlElement(HtmlElement):
    __slots__ = []
    MULTILINE = False

class Raw(Htmlable):
    __slots__ = ["text"]
    def __init__(self, text):
        self.text = str(text)
    def render_html(self):
        return [(-1, False, self.text)]

nbsp = Raw("&nbsp;")
copy = Raw("&copy;")
def escaped(val):
    if isinstance(val, six.string_types):
        val = ord(val[0])
    return Raw("&#%04x;" % (val,))

class Comment(Htmlable):
    __slots__ = ["lines"]
    def __init__(self, lines):
        self.lines = lines
    def render_html(self):
        if not self.lines:
            return
        if len(self.lines) == 1:
            yield 0, True, "<!-- %s -->" % (xml_escape(self.lines[0]).replace("-->", "-- >"))
        else:
            yield 0, False, "<!-- "
            for line in self.lines:
                yield 0, True, xml_escape(line).replace("-->", "-- >")
            yield 0, False, " -->"

class Selector(object):
    __slots__ = ["parent", "names", "properties"]
    def __init__(self, parent, names):
        self.parent = parent
        self.names = names
        self.properties = {}
    def __setitem__(self, name, value):
        self.properties[name] = str(value)
    def render_html(self):
        nesting = [self.names]
        node = self.parent
        while node:
            nesting.append(node.names)
            node = node.parent
        for parts in itertools.product(*reversed(nesting)):
            parts = [(" " if p.strip()[0] not in "+.:>#[]()," else "") + p.strip() for p in parts]
            yield 0, True, "%s {" % ("".join(parts).strip(),)
            for key, val in self.properties.items():
                yield 1, True, "%s: %s;" % (key.rstrip("_").replace("_", "-"), val)
            yield 0, True, "}"

class CSS(Htmlable):
    __slots__ = ["_curr", "_selectors"]
    def __init__(self):
        self._curr = None
        self._selectors = []
    @contextmanager
    def __call__(self, *selectors):
        sel = Selector(self._curr if self._curr else "", selectors)
        self._selectors.append(sel)
        prev = self._curr
        self._curr = sel
        try:
            yield sel
        finally:
            self._curr = prev
    def __setitem__(self, name, value):
        self._curr[name] = value
    def __bool__(self):
        return bool(self._selectors)
    __nonzero__ = __bool__
    
    def render_html(self):
        for sel in self._selectors:
            for level, nl, line in sel.render_html():
                yield level, nl, line


class HtmlDocument(object):
    DOCTYPE = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
    __slots__ = ["__weakref__", "_root", "_stack", "_head_css", "_head", "_body"]
    
    def __init__(self, xmlns = "http://www.w3.org/1999/xhtml"):
        self._root = HtmlElement(weakref.proxy(self), "html", [], attrs = {"xmlns" : xmlns})
        self._stack = [self._root]
        self._head = None
        self._body = None
        self._head_css = None
    
    def __str__(self):
        return self.render()
    def render(self, tabulator = "\t"):
        lines = []
        prev_nl = False
        for level, nl, line in self._root.render_html():
            if not prev_nl and not nl:
                level = 0
            lines.append("%s%s%s" % ("\n" if nl or prev_nl else "", tabulator * level, line))
            prev_nl = nl
        return self.DOCTYPE + "".join(lines)

    def _push(self, elem):
        self._stack.append(elem)
    def _pop(self):
        self._stack.pop(-1)
    def text(self, *texts):
        self._stack[-1].elements.extend(texts)
    def attrs(self, **attrs):
        self._stack[-1].attrs.update(attrs)
    def raw(self, text):
        self._stack[-1].elements.append(Raw(text))
    def comment(self, *lines):
        self._stack[-1].elements.append(Comment(lines))
        
    def subelem(self, tag, *elems, **attrs):
        elem = HtmlElement(weakref.proxy(self), tag, list(elems), attrs)
        self._stack[-1].elements.append(elem)
        return elem
    def inline_subelem(self, tag, *elems, **attrs):
        elem = InlineHtmlElement(weakref.proxy(self), tag, list(elems), attrs)
        self._stack[-1].elements.append(elem)
        return elem
    
    def head_css(self):
        if self._head_css is None:
            self._head_css = CSS()
            with self.head():
                with self.style():
                    self._stack[-1].elements.append(self._head_css)
        return self._head_css
    
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return partial(self.subelem, name)
    
    #===================================================================================================================
    # Elements
    #===================================================================================================================
    def head(self):
        if self._head is None:
            self._head = self.subelem("head")
        return self._head
    def body(self, *texts, **attrs):
        if self._body is None:
            self._body = self.subelem("body", *texts, **attrs)
        return self._body
    
    def meta(self, **attrs):
        return self.subelem("meta", **attrs)
    def title(self, *texts):
        return self.inline_subelem("title", *texts)
    def base(self, **attrs):
        return self.subelem("base", **attrs)
    def link(self, **attrs):
        return self.subelem("link", **attrs)
    def style(self, type_ = "text/css", **attrs):
        return self.subelem("style", type_ = type_, **attrs)
    def script(self, type_ = "text/javascript", **attrs):
        return self.subelem("script", None, type_ = type_, **attrs)
    def link_css(self, href):
        return self.link(href = href, type = "text/css", rel = "stylesheet")
    def script_src(self, src, type_ = "text/javascript"):
        return self.inline_subelem("script", None, type_ = type_, src = src)
    
    def div(self, *texts, **attrs):
        return self.subelem("div", *texts, **attrs)
    def blockquote(self, *texts, **attrs):
        return self.subelem("blockquote", *texts, **attrs)
    def dl(self, *texts, **attrs):
        return self.subelem("dl", *texts, **attrs)
    def dt(self, *texts, **attrs):
        return self.subelem("dt", *texts, **attrs)
    def dd(self, *texts, **attrs):
        return self.subelem("dd", *texts, **attrs)
    def li(self, *texts, **attrs):
        return self.subelem("li", *texts, **attrs)
    def ul(self, *texts, **attrs):
        return self.subelem("ul", *texts, **attrs)
    def ol(self, *texts, **attrs):
        return self.subelem("ol", *texts, **attrs)
    def form(self, *texts, **attrs):
        return self.subelem("form", *texts, **attrs)
    def input(self, *texts, **attrs):
        return self.subelem("input", *texts, **attrs)
    def button(self, *texts, **attrs):
        return self.subelem("button", *texts, **attrs)
    def select(self, *texts, **attrs):
        return self.subelem("select", *texts, **attrs)
    def label(self, *texts, **attrs):
        return self.subelem("label", *texts, **attrs)
    def optgroup(self, *texts, **attrs):
        return self.subelem("optgroup", *texts, **attrs)
    def option(self, *texts, **attrs):
        return self.subelem("option", *texts, **attrs)
    def textarea(self, *texts, **attrs):
        return self.subelem("textarea", *texts, **attrs)
    def legend(self, *texts, **attrs):
        return self.subelem("legend", *texts, **attrs)
    def table(self, *texts, **attrs):
        return self.subelem("table", *texts, **attrs)
    def tr(self, *texts, **attrs):
        return self.subelem("tr", *texts, **attrs)
    def th(self, *texts, **attrs):
        return self.subelem("th", *texts, **attrs)
    def td(self, *texts, **attrs):
        return self.subelem("td", *texts, **attrs)
    def colgroup(self, *texts, **attrs):
        return self.subelem("colgroup", *texts, **attrs)
    def thead(self, *texts, **attrs):
        return self.subelem("thead", *texts, **attrs)
    def tbody(self, *texts, **attrs):
        return self.subelem("tbody", *texts, **attrs)
    def tfoot(self, *texts, **attrs):
        return self.subelem("tfoot", *texts, **attrs)
    def frame(self, *texts, **attrs):
        return self.subelem("frame", *texts, **attrs)
    def iframe(self, *texts, **attrs):
        return self.subelem("iframe", *texts, **attrs)
    def noframe(self, *texts, **attrs):
        return self.subelem("noframe", *texts, **attrs)
    def frameset(self, *texts, **attrs):
        return self.subelem("frameset", *texts, **attrs)
    def p(self, *texts, **attrs):
        return self.subelem("p", *texts, **attrs)
    
    def img(self, *texts, **attrs):
        return self.inline_subelem("img", *texts, **attrs)
    def pre(self, *texts, **attrs):
        return self.inline_subelem("pre", *texts, **attrs)
    def code(self, *texts, **attrs):
        return self.inline_subelem("code", *texts, **attrs)
    def span(self, *texts, **attrs):
        return self.inline_subelem("span", *texts, **attrs)
    def a(self, *texts, **attrs):
        return self.inline_subelem("a", *texts, **attrs)
    def b(self, *texts, **attrs):
        return self.inline_subelem("b", *texts, **attrs)
    def br(self, *texts, **attrs):
        return self.inline_subelem("br", *texts, **attrs)
    def hr(self, *texts, **attrs):
        return self.inline_subelem("hr", *texts, **attrs)
    def em(self, *texts, **attrs):
        return self.inline_subelem("em", *texts, **attrs)
    def strong(self, *texts, **attrs):
        return self.inline_subelem("strong", *texts, **attrs)
    def cite(self, *texts, **attrs):
        return self.inline_subelem("cite", *texts, **attrs)
    def i(self, *texts, **attrs):
        return self.inline_subelem("i", *texts, **attrs)
    def u(self, *texts, **attrs):
        return self.inline_subelem("u", *texts, **attrs)
    def sub(self, *texts, **attrs):
        return self.inline_subelem("sub", *texts, **attrs)
    def sup(self, *texts, **attrs):
        return self.inline_subelem("sup", *texts, **attrs)
    def big(self, *texts, **attrs):
        return self.inline_subelem("big", *texts, **attrs)
    def small(self, *texts, **attrs):
        return self.inline_subelem("small", *texts, **attrs)
    def h1(self, *texts, **attrs):
        return self.inline_subelem("h1", *texts, **attrs)
    def h2(self, *texts, **attrs):
        return self.inline_subelem("h2", *texts, **attrs)
    def h3(self, *texts, **attrs):
        return self.inline_subelem("h3", *texts, **attrs)
    def h4(self, *texts, **attrs):
        return self.inline_subelem("h4", *texts, **attrs)
    def h5(self, *texts, **attrs):
        return self.inline_subelem("h5", *texts, **attrs)
    def h6(self, *texts, **attrs):
        return self.inline_subelem("h6", *texts, **attrs)



#if __name__ == "__main__":
#    doc = HtmlDocument()
#    
#    with doc.head():
#        with doc.title():
#            doc.text("moshe")
#        css = doc.head_css()
#        with css("div"):
#            css["display"] = "block"
#            with css(".foobar", ".spam"):
#                with css(".bacon"):
#                    css["color"] = "white"
#                css["background_color"] = "black"
#
#    with doc.body():
#        with doc.p():
#            doc.text("hello")
#            doc.b("world")
#            doc.text("zorld")
#            doc.text("forld")
#        with doc.p():
#            with doc.pre():
#                doc.text("""def foo(x, y):
#  return x&y""")
#        with doc.div(class_ = "foobar"):
#            doc.text(copy, "2013")
#        doc.script_src("http://foo/bar.js")
#    print doc.render_html(tabulator = "  ")







