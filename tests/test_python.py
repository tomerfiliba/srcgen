from __future__ import with_statement
import unittest
from srcgen.python import PythonModule, R, E, CythonModule


class TestPython(unittest.TestCase):
    def test(self):
        m = PythonModule()
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
        m.sep()
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

print 'papa'
"""
        self.assertEqual(str(m), output)
    
    def gen_class(self, m, name, *args):
        with m.class_(name):
            with m.method("__init__", *args):
                for a in args:
                    m.stmt("self.{0} = {0}", a)
    
    def test_methods(self):
        m = PythonModule()
        self.gen_class(m, "MyClass", "a", "b")
        self.gen_class(m, "YourClass", "a", "b", "c")
        output = """\
class MyClass(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

class YourClass(object):
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
"""
        self.assertEqual(str(m), output)
    
    def test_cython(self):
        m = CythonModule()
        with m.def_("pyfunc", "a", "b"):
            m.return_("a+b")
        with m.cdef("int cfunc", "int a", "int b"):
            m.return_("a+b")
        with m.cdef.class_("MyCClass"):
            with m.method("spam", "x"):
                m.return_("x * 2")
        with m.cdef.extern("myheader.h"):
            with m.struct("mystruct"):
                m.stmt("int a")
                m.stmt("int b")
                m.stmt("int c")
        
        output = """\
def pyfunc(a, b):
    return a+b

cdef int cfunc(int a, int b):
    return a+b

cdef class MyCClass(object):
    def spam(self, x):
        return x * 2

cdef extern from "myheader.h"
    struct mystruct:
        int a
        int b
        int c
"""
        self.assertEqual(str(m), output)


if __name__ == "__main__":
    unittest.main()


