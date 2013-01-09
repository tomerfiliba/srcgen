#!/usr/bin/env python
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

HERE = os.path.dirname(__file__)

setup(name = "srcgen",
    version = "0.1",
    description = "srcgen: The semantic source code generation framework",
    author = "Tomer Filiba",
    author_email = "tomerfiliba@gmail.com",
    license = "MIT",
    url = "",
    packages = ["srcgen"],
    provides = ["srcgen"],
    requires = ["six"],
    install_requires = ["six"],
    keywords = "source, code, generation, programmatic, semantic",
    long_description = open(os.path.join(HERE, "README.rst"), "r").read(),
    classifiers = [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
    ],
)

