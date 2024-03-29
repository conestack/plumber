from plumber import compat
from pprint import pprint
import doctest
import sys
import unittest


optionflags = (
    doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS | doctest.REPORT_ONLY_FIRST_FAILURE
)


if not compat.IS_PY2 and not compat.IS_PYPY:  # pragma: no cover
    TESTFILES = ['../../../README.rst', '../behavior.py', '../instructions.py']
else:  # pragma: no cover
    TESTFILES = []


def test_suite():
    from plumber.tests import test_plumber

    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(test_plumber))
    suite.addTests(
        [
            doctest.DocFileSuite(
                testfile, globs=dict(pprint=pprint), optionflags=optionflags
            )
            for testfile in TESTFILES
        ]
    )
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    result = runner.run(test_suite())
    sys.exit(not result.wasSuccessful())
