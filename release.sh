#!/bin/sh
rm -rf dist
rm -rf build
rm -rf *.egg-info
python setup.py register
python setup.py sdist --formats=zip,gztar bdist_wininst --plat-name=win32 upload
rm -rf *.egg-info
