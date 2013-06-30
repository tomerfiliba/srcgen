from __future__ import with_statement
import unittest
from srcgen.html import HtmlDocument
from srcgen.js import JS


class TestPython(unittest.TestCase):
    def test_basic(self):
        doc = HtmlDocument()
        with doc.head():
            doc.title("das title")
            doc.link(rel = "foobar", type="text/css")
        
        with doc.body():
            with doc.h1(class_="the_header"):
                doc.text("hello", "world")
            with doc.p():
                doc.text("i am a para&graph\nwith newl<i>nes")
                doc.raw("&nbsp;")
                doc.attrs(data_role = "description")
        
        self.assertEquals(doc.render("    "), """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>das title</title>
        <link type="text/css" rel="foobar"/>
    </head>
    <body>
        <h1 class="the_header">helloworld</h1>
        <p data-role="description">
            i am a para&amp;graph
with newl&lt;i&gt;nes&nbsp;
        </p>
    </body>
</html>""")
        
    def test_css(self):
        doc = HtmlDocument()
        with doc.head():
            doc.title("das title")
            doc.link(rel = "foobar", type="text/css")
        
        css = doc.head_css()
        with css("div"):
            with css("a", "a:hover", "a:visited"):
                with css(".foo"):
                    css["backgroun-color"] = "black"                    
                css["color"] = "#aabbcc"
        
        with doc.body():
            with doc.div():
                doc.a("link1", href = "http://www.google.com")
                doc.a("link2", href = "http://www.google.com", class_="foo")
                doc.a("link3", href = "http://www.google.com")

        self.assertEquals(doc.render("    "), """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>das title</title>
        <link type="text/css" rel="foobar"/>
        <style type="text/css">
            div {
            }
            div a {
                color: #aabbcc;
            }
            div a:hover {
                color: #aabbcc;
            }
            div a:visited {
                color: #aabbcc;
            }
            div a.foo {
                backgroun-color: black;
            }
            div a:hover.foo {
                backgroun-color: black;
            }
            div a:visited.foo {
                backgroun-color: black;
            }
        </style>
    </head>
    <body>
        <div>
            <a href="http://www.google.com">link1</a><a class="foo" href="http://www.google.com">link2</a><a href="http://www.google.com">link3</a>
        </div>
    </body>
</html>""")
    
    def test_js(self):
        doc = HtmlDocument()
        with doc.head():
            doc.title("das title")
            with doc.script():
                m = JS()
                with m.func("onclick", "self"):
                    m.stmt("alert('oh no')")
                    with m.if_("self > 'foo'"):
                        m.return_(17)
                    with m.else_():
                        m.return_(18)
                doc.text(m)

        with doc.body():
            with doc.div():
                pass
        
        self.assertEquals(doc.render("    "), """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>das title</title>
        <script type="text/javascript">
            function onclick(self) {
                alert(&apos;oh no&apos;);
                if (self &gt; &apos;foo&apos;) {
                    return 17;
                }
                else {
                    return 18;
                }
            }
        </script>
    </head>
    <body>
        <div/>
    </body>
</html>""")
        
    def test_comments(self):
        doc = HtmlDocument()
        with doc.head():
            doc.title("das title")
            doc.comment("hello")
            doc.comment("hello", "world")
        
        self.assertEquals(doc.render("    "), """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>das title</title>
        <!-- hello -->
        <!-- 
        hello
        world
         -->
    </head>
</html>""")        



if __name__ == "__main__":
    unittest.main()


