from pprint import pprint
import doctest
import sys
import unittest


optionflags = (
    doctest.NORMALIZE_WHITESPACE
    | doctest.ELLIPSIS
    | doctest.REPORT_ONLY_FIRST_FAILURE
)


if sys.version_info[0] >= 3:  # pragma: no cover
    TESTFILES = [
        '../../../README.rst',
        '../behavior.py',
        '../instructions.py'
    ]
else:  # pragma: no cover
    TESTFILES = []


def test_suite():
    from plumber.tests import test_plumber
    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(test_plumber))
    suite.addTests([
        doctest.DocFileSuite(
            testfile,
            globs=dict(pprint=pprint),
            optionflags=optionflags
        )
        for testfile in TESTFILES
    ])
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(test_suite())
