from __future__ import with_statement
import unittest
from srcgen.python import PythonModule, STMT, SEP, COMMENT, IF, DEF, RETURN


class TestPython(unittest.TestCase):
    def test(self):
        with PythonModule("foo") as mod:
            STMT("import sys")
            STMT("import os")
            SEP()
            COMMENT("hi there", box = True)
            STMT("x = 18")
            with IF("x > 5"):
                STMT("print '''hello\nworld'''")
                with IF("z == 18"):
                    COMMENT("foo", "bar")
                    STMT("print 'lala'")
                with IF("z == 19"):
                    STMT("print 'gaga'")
                STMT("print 'zaza'")
            with DEF("foo", ["a", "b", "c"]):
                STMT("return a + b + c")
            with DEF("bar", ["a", "b", "c"]):
                RETURN("a * b * c")
            STMT("print 'papa'")
        
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
    if z == 18:
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
        
        self.assertEqual(str(mod), output)

if __name__ == "__main__":
    unittest.main()


