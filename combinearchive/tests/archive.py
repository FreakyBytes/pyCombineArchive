"""
Test Classes for reading, writing and manipulating COMBINE archives
no metadata tests involved
"""
import shutil
import os
import tempfile
import unittest
from test import test_support

from combinearchive import combinearchive, metadata


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

        self._temp_files = list()

    def tearDown(self):
        # close archive and remove temp file
        self.close_archive()
        os.remove(self.archive_location)

        # remove created temp files
        for name in self._temp_files:
            os.remove(name)

    def open_archive(self):
        self.carchive = combinearchive.CombineArchive(self.archive_location)
        return self.carchive

    def close_archive(self):
        if hasattr(self, 'carchive') and self.carchive is not None:
            self.carchive.close()

    def get_random_file(self):
        file = tempfile.NamedTemporaryFile(delete=False)
        file.write("pyCombineArchive Test file")
        name = file.name
        self._temp_files.append(name)
        file.close()

        return name

class ReadTest(BaseReadTest):
    TEST_ARCHIVE = '../../test/all-singing-all-dancing.omex'

    def test_get_entry(self):
        self.open_archive()

        entry = self.carchive.get_entry('documentation/Calzone2007.pdf')
        self.assertIsNotNone(entry, 'archive entry is unexpected None. Should throw KeyError instead')

        with self.assertRaises(KeyError):
            self.carchive.get_entry('does not exist')

        self.close_archive()

    def test_filter_format(self):
        self.open_archive()

        test_format = 'http://purl.org/NET/mediatypes/application/pdf'
        filter_result = self.carchive.filter_format(test_format, regex=False)
        for entry in filter_result:
            self.assertEqual(entry.format, test_format, 'filter_format mismatched {}'.format(entry.format))

        self.close_archive()


class AddDeleteTest(BaseReadTest):
    TEST_ARCHIVE = '../../test/all-singing-all-dancing.omex'

    def test_add(self):
        self.open_archive()

        entry = self.carchive.add_entry(self.get_random_file(), "text/plain", "test/1.txt")
        self.assertIsNotNone(entry, 'created entry is None')

        meta = metadata.OmexMetaDataObject()
        meta.creator.append(metadata.VCard(family_name="Peters", given_name="Martin", organization="University of Rostock"))
        meta.creator.append(metadata.VCard(family_name="Scharm", given_name="Martin", organization="University of Rostock"))
        meta.modified.append(meta.created)
        meta.description = "This is a Test"
        entry.add_description(meta)

        self.carchive.pack()



        self.close_archive()


def do_tests():
    """
    run all tests in this module
    """
    test_support.run_unittest(ReadTest,
                              AddDeleteTest)

if __name__ == '__main__':
    do_tests()
