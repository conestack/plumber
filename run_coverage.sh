#!/bin/sh
if [ -x "$(which python)" ]; then
    ./py2/bin/coverage run -m plumber.tests.test_plumber
    ./py2/bin/coverage report
fi
if [ -x "$(which python3)" ]; then
    ./py3/bin/coverage run -m plumber.tests.test_plumber
    ./py3/bin/coverage report
fi
if [ -x "$(which pypy)" ]; then
    ./pypy/bin/coverage run -m plumber.tests.test_plumber
    ./pypy/bin/coverage report
fi
