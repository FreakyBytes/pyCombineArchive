import os
import shutil
import tempfile
import re
from StringIO import StringIO
# import zipfile
import custom_zip as zipfile
from xml.etree import ElementTree
try:
    # Python 3
    from urllib.parse import urlparse, urljoin
except ImportError:
    # Python 2
    from urlparse import urlparse, urljoin

import metadata
import utils
import exceptions

# XML names
_XML_ROOT_ELEM = 'omex:omexManifest'
_XML_ROOT_NS = 'http://identifiers.org/combine.specifications/omex-manifest'
_XML_CONTENT_TAG = 'omex:content'
_XML_CONTENT_LOCATION = 'omex:location'
_XML_CONTENT_FORMAT = 'omex:format'
_XML_CONTENT_MASTER = 'omex:master'
_XML_CONTENT_ARCHIVE_TYPE = 'http://identifiers.org/combine.specifications/omex'
_XML_CONTENT_METADATA_TYPE = 'http://identifiers.org/combine.specifications/omex-metadata'
_XML_NS = {
    'omex': _XML_ROOT_NS,
    metadata.Namespace.RDF: metadata.Namespace.RDF_URI,
    metadata.Namespace.DC: metadata.Namespace.DC_URI,
    metadata.Namespace.VCARD: metadata.Namespace.VCARD_URI,
    metadata.Namespace.BQMODEL: metadata.Namespace.BQMODEL_URI,
}

# register namespaces to ElementTree
for prefix, url in _XML_NS.items():
    ElementTree.register_namespace(prefix, url)


class CombineArchive(metadata.MetaDataHolder):
    """
    base class for reading, creating and modifying COMBINE Archives
    """
    # location of manifest and metadata
    MANIFEST_LOCATION = 'manifest.xml'
    METADATA_LOCATION = 'metadata.rdf'
    # paths used in the manifest to assign meta data to the archive itself
    ARCHIVE_REFERENCE = ('.', '/')

    def __init__(self, archive):
        super(CombineArchive, self).__init__()
        self._archive = archive
        self._zip = zipfile.ZipFile(archive, mode='a')
        self.entries = dict()

        self._read_manifest()
        self._read_metadata()

    def __exit__(self):
        self.close()

    def _read_manifest(self):
        """
        internal function.
        Reads the manifest file of a COMBINE Archive
        """
        try:
            with self._zip.open(self.MANIFEST_LOCATION) as manifest_file:
                manifest = ElementTree.fromstring(manifest_file.read())
        except KeyError:
            # manifest does not exists, probably an empty/new archive
            return False
        except ElementTree.ParseError as e:
            raise exceptions.CombineArchiveException('Cannot parse xml manifest. {}'.format(e.msg))

        # check for correct root element and namespace
        if manifest.tag != utils.extend_tag_name(_XML_ROOT_ELEM, _XML_NS):
            raise exceptions.CombineArchiveException('manifest has no valid omex root element')

        # check entries
        for entry in manifest.findall(_XML_CONTENT_TAG, _XML_NS):
            try:
                location = utils.get_attribute(entry, _XML_CONTENT_LOCATION, _XML_NS)
                entry_format = utils.check_format(utils.get_attribute(entry, _XML_CONTENT_FORMAT, _XML_NS), convert=False)
                master = True if entry.attrib.get(_XML_CONTENT_MASTER, False) in ('True', 'true', True) else False
            except KeyError:
                raise exceptions.CombineArchiveException('location and format field are required. Corrupt manifest.xml')

            # clean location
            location = utils.clean_pathname(location)

            # check if file is in zip, if it's not the root element
            zipinfo = None
            if location not in self.ARCHIVE_REFERENCE:
                try:
                    zipinfo = self._zip.getinfo(location)
                except KeyError:
                    raise exceptions.CombineArchiveException(
                        '{location} is specified by the manifest, but not contained by the ZIP file'.format(location=location))

            archive_entry = ArchiveEntry(location, format=entry_format, master=master, archive=self, zipinfo=zipinfo)
            self.entries[location] = archive_entry

    def _read_metadata(self):

        # go over all possible metdata files
        for meta_file in self.filter_format(_XML_CONTENT_METADATA_TYPE):
            try:
                # parse the xml
                meta = ElementTree.fromstring(meta_file.read())
            except ElementTree.ParseError as e:
                raise exceptions.CombineArchiveException(
                    'Cannot parse xml metadata {file}. {msg}'.format(file=meta_file.location, msg=e.msg))

            # find every rdf:Description
            for description in meta.findall(metadata.Namespace.rdf_terms.description, _XML_NS):
                try:
                    about_url = urlparse(utils.get_attribute(description, metadata.Namespace.rdf_terms.about, _XML_NS))
                    about_str = about_url.path
                    fragment_str = about_url.fragment
                except KeyError:
                    raise exceptions.CombineArchiveException('A metadata description tag has to have an about field')

                if about_str in self.ARCHIVE_REFERENCE:
                    # meta data is about the archive (root element)
                    about = self
                else:
                    # meta data is about normal file
                    about = self.get_entry(about_str)

                # start parsing
                try:
                    data = metadata.OmexMetaDataObject(description)
                except ValueError as e:
                    data = metadata.DefaultMetaDataObject(description)

                about.add_description(data, fragment=fragment_str)

    def _write_manifest(self, zip_file=None):
        """
        internal function.
        Writes the manifest file of a COMBINE Archive
        """
        if zip_file is None:
            zip_file = self._zip

        # create new DOM object
        manifest = ElementTree.Element(utils.extend_tag_name(_XML_ROOT_ELEM, _XML_NS))

        # write first entry for archive itself
        content = ElementTree.SubElement(manifest, utils.extend_tag_name(_XML_CONTENT_TAG, _XML_NS))
        content.attrib.update({
            utils.extend_tag_name(_XML_CONTENT_LOCATION, _XML_NS): '.',
            utils.extend_tag_name(_XML_CONTENT_FORMAT, _XML_NS): _XML_CONTENT_ARCHIVE_TYPE,
        })

        for (location, entry) in self.entries.items():
            entry_format = utils.check_format(entry.format)
            content = ElementTree.SubElement(manifest, utils.extend_tag_name(_XML_CONTENT_TAG, _XML_NS))
            content.attrib.update({
                utils.extend_tag_name(_XML_CONTENT_LOCATION, _XML_NS): location,
                utils.extend_tag_name(_XML_CONTENT_FORMAT, _XML_NS): entry_format,
            })
            if entry.master:
                content.attrib[utils.extend_tag_name(_XML_CONTENT_MASTER, _XML_NS)] = True

        # write xml to zip
        io = StringIO()
        ElementTree.ElementTree(manifest).write(io, xml_declaration=True, default_namespace=_XML_ROOT_NS)
        zip_file.writestr(self.MANIFEST_LOCATION, io.getvalue())
        io.close()

    def _write_metadata(self, zip_file=None):

        if zip_file is None:
            zip_file = self._zip

        # create new Element object for RDF
        rdf = ElementTree.Element(utils.extend_tag_name(metadata.Namespace.rdf_terms.rdf, _XML_NS))

        # iterate over all metadata for each entry
        for (location, entry) in self.entries.items():
            if not isinstance(entry, metadata.MetaDataHolder):
                continue
            for description in entry.description:
                desc_elem = description._rebuild_xml()
                desc_elem.attrib[utils.extend_tag_name(metadata.Namespace.rdf_terms.about, _XML_NS)] = location
                rdf.append(desc_elem)

        # write xml to zip
        io = StringIO()
        ElementTree.ElementTree(rdf).write(io, xml_declaration=True)
        self.add_entry(io.getvalue(), _XML_CONTENT_METADATA_TYPE, location=self.METADATA_LOCATION, replace=True)
        #zip_file.writestr(self.METADATA_LOCATION, xmlstring)
        io.close()

    def close(self):
        """
        closes the COMBINE Archive.
        Does not write any changes to the manifest. Needs to be invoked by pack()
        """
        self._zip.close()

    def pack(self):
        """
        writes any change of manifest or metadate into the COMBINE archive
        """
        try:
            new_file = tempfile.NamedTemporaryFile(
                dir=os.path.dirname(self._archive), delete=False )
        except:
            new_file = tempfile.NamedTemporaryFile(delete=False)

        new_zip = zipfile.ZipFile(new_file, mode='a')

        # add main entries
        self._write_metadata(zip_file=new_zip)  # write metadata first, so the ArchiveEntry is updated
        self._write_manifest(zip_file=new_zip)

        # add all entries
        for (location, entry) in self.entries.items():
            if location in self.ARCHIVE_REFERENCE or location == self.MANIFEST_LOCATION:
                # skip root entry (representing the archive itself) and the two main entries (manifest and metadata)
                continue

            if entry.zipinfo is None:
                entry.zipinfo = self._zip.getinfo(location)

            buffer = self._zip.read(entry.zipinfo)
            new_zip.writestr(entry.zipinfo, buffer)

        # close both zip files
        new_zip.close()
        self._zip.close()

        # remove old file and move new one
        os.remove(self._archive)
        #print ''.join(('new file name: ', new_file.name))
        #print ''.join(('archive name:  ', self._archive))
        shutil.move(new_file.name, self._archive)

        # open new zip file
        self._zip = zipfile.ZipFile(self._archive, mode='a')

    def add_entry(self, file, format, location=None, master=False, replace=False):
        """
        adds a file to the COMBINE archive and adds a manifest entry

        Returns:
            ArchiveEntry
        """
        if not file or not format:
            raise exceptions.CombineArchiveException('both a file and the corresponding format must be provided')
        # check format schema
        format = utils.check_format(format)

        # no location provided. Guess it
        if location is None or not location:
            location = os.path.basename(file)

        # clean location
        location = utils.clean_pathname(location)

        if location == self.MANIFEST_LOCATION or location in self.ARCHIVE_REFERENCE:
            raise exceptions.CombineArchiveException('it is not allowed to name a file {loc}'.format(loc=location))

        if location in self._zip.namelist():
            if replace is False:
                raise exceptions.CombineArchiveException('{loc} exists already in the COMBINE archive. set replace=True, to override it'.format(loc=location))
            else:
                self.remove_entry(location)

        # write file to zip
        if isinstance(file, (str, unicode)):
            # file is actually string
            zipinfo = self._zip.writestr(location, file)
        else:
            zipinfo = self._zip.write(file, location)

        entry = ArchiveEntry(location, format=format, master=master, zipinfo=zipinfo)
        self.entries[entry.location] = entry
        return entry

    def remove_entry(self, location):
        """
        Removes an entry from the COMBINE archive. The file will remain in the
        zip archive, until pack() is called.
        """
        location = utils.clean_pathname(location)
        if self.entries[location]:
            del self.entries[location]
        else:
            raise KeyError('Did not found {loc} in COMBINE archive'.format(loc=location))

    def get_entry(self, location):
        """
        Returns the archive entry in the given location or raises an KeyError,
        if not found
        """
        location = utils.clean_pathname(location)
        if self.entries[location]:
            return self.entries[location]
        else:
            raise KeyError('Did not found {loc} in COMBINE archive'.format(loc=location))

    def filter_format(self, format, regex=False):
        """
        Generator including all archive entries with a given format.
        Is regex=True, format will be compiled to a regual expression and
        matched against the entry formats
        """
        if not format:
            raise KeyError('You need to provide an format')

        # check format argument against spec
        try:
            utils.check_format(format)
        except exceptions.CombineArchiveFormatException as e:
            raise KeyError('{format} is no valid format, according to the OMEX specification. {cause}'.format(format=format, cause=e.message))

        if regex is True:
            pattern = re.compile(format)
        else:
            pattern = None

        for (location, entry) in self.entries.items():
            if pattern is not None and pattern.match(entry.format):
                yield entry
            elif pattern is None and format == entry.format:
                yield entry

    def get_master_entries(self):
        """
        Returns a list of entries with set master flag
        """
        return [entry for entry in self.entries.values() if entry.master is True]


class ArchiveEntry(metadata.MetaDataHolder):
    """
    represents a single entry in a COMBINE archive
    """
    def __init__(self, location, format=None, master=False, zipinfo=None, archive=None):
        super(ArchiveEntry, self).__init__()
        self.location = location
        self.format = format
        self.master = master
        self.archive = archive
        self.zipinfo = zipinfo

    def read(self):
        if self.zipinfo is not None and self.archive is not None:
            return self.archive._zip.read(self.zipinfo)
        elif self.zipinfo is None and self.archive is not None:
            return self.archive._zip.read(self.location)
        else:
            raise exceptions.CombineArchiveException('There is no reference back to the Combine archive')
