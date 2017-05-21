#!/bin/sh
if [ -x "$(which python)" ]; then
    rm -r py2
    virtualenv --clear --no-site-packages -p python py2
    ./py2/bin/python setup.py develop
    ./py2/bin/pip install coverage zope.interface
fi
if [ -x "$(which python3)" ]; then
    rm -r py3
    virtualenv --clear --no-site-packages -p python3 py3
    ./py3/bin/python setup.py develop
    ./py3/bin/pip install coverage zope.interface
fi
if [ -x "$(which pypy)" ]; then
    rm -r pypy
    virtualenv --clear --no-site-packages -p pypy pypy
    ./pypy/bin/python setup.py develop
    ./pypy/bin/pip install coverage zope.interface
fi
