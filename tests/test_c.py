from __future__ import with_statement
import unittest
from srcgen.c import CModule, E


class TestC(unittest.TestCase):
    def test(self):
        m = CModule("foo")
        m.include("<stdio.h>")
        m.include("<inttypes.h>")
        m.sep()
        m.comment("this is a simple comment")
        with m.enum("weekdays"):
            m.enum_member("sun")
            m.enum_member("mon")
            m.enum_member("tue")
            m.enum_member("wed")
        
        m.comment("this is a boxed comment", box = True)
        with m.typedef_union("foo"):
            with m.struct("", "raw"):
                m.stmt("uint64_t a")
                m.stmt("uint64_t b")
                m.stmt("uint64_t c")
                m.stmt("uint64_t d")
        
        m.comment("this is a sep comment", sep = True)
        with m.func("int", "main", "int argv", "const char ** argc"):
            with m.if_(E("x") > 5):
                m.stmt(E("printf")("hi"))
        output = """\
#include <stdio.h>
#include <inttypes.h>

/* this is a simple comment */
enum weekdays {
    sun,
    mon,
    tue,
    wed
};

/* ******************************************************************************
/* this is a boxed comment
****************************************************************************** */
typedef union _foo {
    struct  {
        uint64_t a;
        uint64_t b;
        uint64_t c;
        uint64_t d;
    } raw;

} foo;

/*
/* this is a sep comment
*/
int main(int argv, const char ** argc) {
    if ((x > 5)) {
        printf("hi");
    }
}
"""
        self.assertEqual(str(m), output)


if __name__ == "__main__":
    unittest.main()


