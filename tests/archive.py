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
    TEST_ARCHIVE = None

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
    TEST_ARCHIVE = 'tests/data/all-singing-all-dancing.omex'

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
    TEST_ARCHIVE = None #'tests/data/all-singing-all-dancing.omex'

    def test_add_delete(self):
        self.open_archive()
        test_file_name = "test/1.txt"

        entry = self.carchive.add_entry(self.get_random_file(), "text/plain", test_file_name)
        self.assertIsNotNone(entry, 'created entry is None')

        meta = metadata.OmexMetaDataObject()
        meta.creator.append(metadata.VCard(family_name="Peters", given_name="Martin", organization="University of Rostock", email="mail@mail.org"))
        meta.creator.append(metadata.VCard(family_name="Scharm", given_name="Martin", organization="University of Rostock"))
        meta.modified.append(meta.created)
        meta.description = "This is a Test"
        entry.add_description(meta)

        self.carchive.pack()
        self.carchive.close()
        self.carchive = combinearchive.CombineArchive(self.archive_location)

        entry = self.carchive.get_entry(test_file_name)
        self.assertIsNotNone(entry, 'Formerly added entry not found in the archive')
        desc = entry.description[0]

        # checking meta data
        self.assertEqual(desc.created, desc.modified[0], 'create and modified date in OmexDescription should be equal')

        self.assertEqual(desc.creator[0].family_name, 'Peters')
        self.assertEqual(desc.creator[0].given_name, 'Martin')
        self.assertEqual(desc.creator[0].organization, 'University of Rostock')
        self.assertEqual(desc.creator[0].email, 'mail@mail.org')

        self.assertEqual(desc.creator[1].family_name, 'Scharm')
        self.assertEqual(desc.creator[1].given_name, 'Martin')
        self.assertEqual(desc.creator[1].organization, 'University of Rostock')

        # check removal of entry
        self.carchive.remove_entry(test_file_name)

        self.carchive.pack()
        self.close_archive()


class FormatConversionTest(unittest.TestCase):

    def test_formatcheck(self):

        with self.assertRaises(combinearchive.CombineArchiveFormatException):
            combinearchive.check_format('foobar', convert=False)                        # no mime type or url
        with self.assertRaises(combinearchive.CombineArchiveFormatException):
            combinearchive.check_format('ftp://purl.org/mediatypes/application/pdf')    # not a valid url schema (only https? allowed)

        # check for identifiers urls
        self.assertEqual(combinearchive.check_format('http://identifiers.org/combine.specifications/cellml'),
                         'http://identifiers.org/combine.specifications/cellml',
                         'check_format alternated identifiers.org link')

        self.assertEqual(combinearchive.check_format('http://identifiers.org/combine.specifications/sbml.level-3.version-1'),
                         'http://identifiers.org/combine.specifications/sbml.level-3.version-1',
                         'check_format alternated identifiers.org link')

    def test_conversion(self):

        # no conversion, but check of mime type
        self.assertEqual(combinearchive.check_format('application/pdf', convert=False),
                         'application/pdf')

        # conversion to purl.org url
        self.assertEqual(combinearchive.check_format('application/pdf', convert=True),
                         'http://purl.org/NET/mediatypes/application/pdf')


def do_tests():
    """
    run all tests in this module
    """
    test_support.run_unittest(ReadTest,
                              AddDeleteTest,
                              FormatConversionTest)

if __name__ == '__main__':
    do_tests()
