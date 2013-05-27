srcgen
======

Srcgen is a **semantic** code generation framework. Being semantic means that the code generator and the
generated code bear similar structure, as well ; for instance, the body of an ``if`` statement is indented both in
the generating and generated code. Here's a short example::

    >>> from srcgen.python import PythonModule
    >>>
    >>> m = PythonModule("foo")
    >>> m.import_("sys")
    >>> m.import_("os")
    >>> m.sep()
    >>> m.stmt("x = 5")
    >>> with m.if_("x > 8"):
    ...     m.stmt("print 'oh no'")
    ...
    >>> with m.else_():
    ...     m.stmt("print 'oh yes'")
    ...
    >>> print m
    import sys
    import os
    
    x = 5
    if x > 8:
        print 'oh no'
    else:
        print 'oh yes'

You can nest deeper, of course, as well as extract common pieces of code into functions:: 

    m = PythonModule("foo")
    with m.class_("MyClass"):
        with m.method("__init__", "




Languages
=========
At the moment Srcgen supports:

* C
* Python
* Cython
* HTML/XML

More languages will be added per public demand (you're welcome to join the effort!)





