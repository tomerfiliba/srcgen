from __future__ import with_statement
import unittest
from srcgen.python import PythonModule, R, P, E


class TestPython(unittest.TestCase):
    def test(self):
        m = PythonModule("foo")
        m.stmt("import sys")
        m.stmt("import os")
        m.sep()
        m.comment("hi there", box = True)
        m.stmt(R(x = 18))
        with m.if_("x > 5"):
            m.stmt("print '''hello\nworld'''")
            with m.if_(E("z") == 18):
                m.comment("foo", "bar")
                m.stmt("print 'lala'")
            with m.if_("z == 19"):
                m.stmt("print 'gaga'")
            m.stmt("print 'zaza'")
        with m.def_("foo", "a", "b", "c"):
            m.stmt("return a + b + c")
        with m.def_("bar", "a", "b", "c"):
            m.return_("a * b * c")
        m.stmt("print 'papa'")
    
        output = """\
import sys
import os

################################################################################
# hi there
################################################################################
x = 18
if x > 5:
    print '''hello
world'''
    if (z == 18):
        # foo
        # bar
        print 'lala'
    if z == 19:
        print 'gaga'
    print 'zaza'
def foo(a, b, c):
    return a + b + c

def bar(a, b, c):
    return a * b * c

print 'papa'"""

        self.assertEqual(str(m), output)


if __name__ == "__main__":
    unittest.main()


