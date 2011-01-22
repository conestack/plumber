import unittest
import doctest 
from pprint import pprint
from interlude import interact

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE

TESTFILES = [
    '../plumber.txt',
]

def test_suite():
    return unittest.TestSuite([
        doctest.DocFileSuite(
            file, 
            optionflags=optionflags,
            globs={'interact': interact,
                   'pprint': pprint},
            ) for file in TESTFILES
        ]+[
        doctest.DocTestSuite(
            'plumber.tests._globalmetaclasstest',
            )
    ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
