"""
Test Classes for reading, writing and manipulating COMBINE archives
no metadata tests involved
"""
import shutil
import os
import tempfile
import unittest
from test import test_support

import combinearchive.combinearchive as combinearchive


class ReadTest(unittest.TestCase):
    """
    abstract base class for all tests involve only reading from COMBINE archives
    """

    def setUp(self):
        # first copy test archive into a temp location, so validation data does
        # not get harmed
        self.archive_location = tempfile.NamedTemporaryFile(delete=False).name
        shutil.copy('test.omex', self.archive_location)
        self.carchive = combinearchive.CombineArchive(self.archive_location)
        pass

    def tearDown(self):
        # close archive and remove temp file
        self.carchive.close()
        os.remove(self.archive_location)
        pass


def do_tests():
    """
    run all tests in this module
    """
    test_support.run_unittest(ReadTest,
                              )

if __name__ == '__main__':
    do_tests()
