#!/bin/sh
./$1/bin/coverage run -m plumber.tests.__init__
./$1/bin/coverage report
./$1/bin/coverage html
