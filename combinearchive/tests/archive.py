"""
Test Classes for reading, writing and manipulating COMBINE archives
no metadata tests involved
"""
import unittest
from test import test_support

import combinearchive.combinearchive as combinearchive


class ReadTest(unittest.TestCase):
    """
    abstract base class for all tests involve only reading from COMBINE archives
    """

    def setUp(self):
        self.carchive = combinearchive.CombineArchive('test.omex')
        pass

    def tearDown(self):
        self.carchive.close()
        pass


def do_tests():
    """
    run all tests in this module
    """
    test_support.run_unittest(ReadTest,
                              )

if __name__ == '__main__':
    do_tests()
