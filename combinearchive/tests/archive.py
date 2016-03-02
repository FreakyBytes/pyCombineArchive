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


class BaseReadTest(unittest.TestCase):
    """
    abstract base class for all tests involve only reading from COMBINE archives
    """
    TEST_ARCHIVE = 'test.omex'

    def setUp(self):
        # first copy test archive into a temp location, so validation data does
        # not get harmed
        self.archive_location = tempfile.NamedTemporaryFile(delete=False).name
        if self.TEST_ARCHIVE is not None:
            shutil.copy(self.TEST_ARCHIVE, self.archive_location)

    def tearDown(self):
        # close archive and remove temp file
        self.close_archive()
        os.remove(self.archive_location)

    def open_archive(self):
        self.carchive = combinearchive.CombineArchive(self.archive_location)
        return self.carchive

    def close_archive(self):
        if hasattr(self, 'carchive') and self.carchive is not None:
            self.carchive.close()

class ReadTest(BaseReadTest):
    TEST_ARCHIVE = '../../test/all-singing-all-dancing.omex'

    def test_read_file(self):
        self.open_archive()

        entry = self.carchive.get_entry('documentation/Calzone2007.pdf')
        self.assertIsNotNone(entry, 'archive entry is unexpected None. Should throw KeyError instead')

        self.close_archive()

    def test_file_not_found(self):
        self.open_archive()

        with self.assertRaises(KeyError):
            self.carchive.get_entry('does not exist')

        self.close_archive()


def do_tests():
    """
    run all tests in this module
    """
    test_support.run_unittest(ReadTest,
                              )

if __name__ == '__main__':
    do_tests()
