#!/bin/sh
./$1/bin/coverage run -m plumber.tests.test_plumber
./$1/bin/coverage report
./$1/bin/coverage html
