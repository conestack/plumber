#!/bin/sh
if [ -x "$(which python)" ]; then
    ./py2/bin/python -m plumber.tests.__init__
fi
if [ -x "$(which python3)" ]; then
    ./py3/bin/python -m plumber.tests.__init__
fi
if [ -x "$(which pypy)" ]; then
    ./pypy/bin/python -m plumber.tests.__init__
fi
