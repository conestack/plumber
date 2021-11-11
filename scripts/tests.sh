#!/bin/sh
if [ -x "$(which python)" ]; then
    ./py2/bin/python -m unittest plumber.tests.test_plumber
fi
if [ -x "$(which python3)" ]; then
    ./py3/bin/python -m unittest plumber.tests.test_plumber
fi
if [ -x "$(which pypy)" ]; then
    ./pypy/bin/python -m unittest plumber.tests.test_plumber
fi
