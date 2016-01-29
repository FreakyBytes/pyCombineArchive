import os
import shutil
import tempfile
import re
import zipfile
import xml.dom.minidom as minidom
import metadata


class CombineArchive(metadata.MetaDataHolder):
    """
    base class for reading, creating and modifying COMBINE Archives
    """
    # location of manifest and metadata
    MANIFEST_LOCATION = 'manifest.xml'
    METADATA_LOCATION = 'metadata.rdf'

    # XML names
    _XML_ROOT_ELEM = 'omexManifest'
    _XML_ROOT_NS = 'http://identifiers.org/combine.specifications/omex-manifest'
    _XML_CONTENT_TAG = 'content'
    _XML_CONTENT_LOCATION = 'location'
    _XML_CONTENT_FORMAT = 'format'
    _XML_CONTENT_MASTER = 'master'
    _XML_CONTENT_ARCHIVE_TYPE = 'http://identifiers.org/combine.specifications/omex'
    _XML_CONTENT_METADATA_TYPE = 'http://identifiers.org/combine.specifications/omex-metadata'

    def __init__(self, archive):
        super(CombineArchive, self).__init__(self)
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
                manifest = minidom.parseString( ''.join(manifest_file.readlines()) )
        except KeyError:
            # manifest does not exists, probaply an empty/new archive
            return False

        # check for correct root element and namespace
        root = manifest.documentElement
        if root.tagName != self._XML_ROOT_ELEM or root.getAttribute('xmlns') != self._XML_ROOT_NS:
            raise CombineArchiveException('manifest has no valid omex root element')

        # check entries
        for entry in root.getElementsByTagName(self._XML_CONTENT_TAG):
            location = entry.getAttribute(self._XML_CONTENT_LOCATION)
            format = entry.getAttribute(self._XML_CONTENT_FORMAT)
            master = (True if entry.getAttribute(self._XML_CONTENT_MASTER) == 'True' else False)

            if not location or not format:
                raise CombineArchiveException('location and format field are required. Corrupt manifest.xml')

            # clean location
            location = clean_pathname(location)

            # check if file is in zip
            try:
                self._zip.getinfo(location)
            except KeyError:
                raise CombineArchiveException("{location} is specified by the manifest, but not contained by the ZIP file".format(location=location))

            archive_entry = ArchiveEntry(location, format=format, master=master, archive=self)
            self.entries[location] = archive_entry

    def _read_metadata(self):

        # go over all possible metdata files
        for meta_file in self.filter_format(self._XML_CONTENT_METADATA_TYPE):
            # parse the xml
            meta = minidom.parseString( meta_file.read() )
            # find every rdf:Description
            for description in meta.getElementByTagNameNS(metadata.Namespace.RDF_URI, metadata.Namespace.rdf_terms.description):
                about_str = description.getAttributeNS(metadata.Namespace.RDF_URI, metadata.Namespace.rdf_terms.description)
                if about_str == '.' or about_str == '/':
                    # meta data is about the archive (root element)
                    about = self
                else:
                    # meta data is about normal file
                    about = self.get_entry(about_str)

                # start parsing
                try:
                    data = metadata.OmexMetaDataObject(description)._try_parse()
                except:
                    data = metadata.DefaultMetaDataObject(description)._try_parse()

                # TODO parse fragment
                about.add_description(data)


        pass

    def _write_manifest(self, zip=None):
        """
        internal function.
        Writes the manifest file of a COMBINE Archive
        """
        if zip is None:
            zip = self._zip

        # create new DOM object
        manifest = minidom.getDOMImplementation().createDocument(self._XML_ROOT_NS, self._XML_ROOT_ELEM, None)
        root = manifest.documentElement
        root.setAttribute('xmlns', self._XML_ROOT_NS)

        # write first entry for archive itself
        content = manifest.createElement(self._XML_CONTENT_TAG)
        content.setAttribute(self._XML_CONTENT_LOCATION, '.')
        content.setAttribute(self._XML_CONTENT_FORMAT, self._XML_CONTENT_ARCHIVE_TYPE)
        root.appendChild(content)

        for (location, entry) in self.entries.items():
            format = check_format(entry.format)
            content = manifest.createElement(self._XML_CONTENT_TAG)
            content.setAttribute(self._XML_CONTENT_LOCATION, entry.location)
            content.setAttribute(self._XML_CONTENT_FORMAT, format)
            if entry.master:
                content.setAttribute(self._XML_CONTENT_MASTER, True)

            root.appendChild(content)

        # write xml to zip
        xmlstring = manifest.toprettyxml()
        zip.writestr(self.MANIFEST_LOCATION, xmlstring)

    def _write_metadata(self, zip=None):
        pass

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
        self._write_manifest(zip=new_zip)
        self._write_metadata(zip=new_zip)

        # add all entries
        for (location, entry) in self.entries.items():
            #entry = self.entries[location]
            if entry.zipinfo is None:
                entry.zipinfo = self._zip.getinfo(location)

            buffer = self._zip.read(entry.zipinfo)
            new_zip.writestr(entry.zipinfo, buffer)

        # close both zip files
        new_zip.close()
        self._zip.close()
        new_file.close()

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
            raise CombineArchiveException('both a file and the corresponding format must be provided')
        # check format schema
        format = check_format(format)

        # no location provided. Guess it
        if location is None or not location:
            location = os.path.basename(file)

        # clean location
        location = clean_pathname(location)

        if location == self.MANIFEST_LOCATION or location == self.METADATA_LOCATION:
            raise CombineArchiveException('it is not allowed to name a file {loc}'.format(loc=location))

        if location in self._zip.namelist():
            if replace is False:
                raise CombineArchiveException('{loc} exists already in the COMBINE archive. set replace=True, to override it'.format(loc=location))
            else:
                self.remove_entry(location)

        # write file to zip
        self._zip.write(file, location)
        entry = ArchiveEntry(location, format=format, master=master, zipinfo=self._zip.getinfo(location))
        self.entries[entry.location] = entry
        return entry

    def remove_entry(self, location):
        """
        Removes an entry from the COMBINE archive. The file will remain in the
        zip archive, until pack() is called.
        """
        location = clean_pathname(location)
        if self.entries[location]:
            del self.entries[location]
        else:
            raise KeyError('Did not found {loc} in COMBINE archive'.format(loc=location))

    def get_entry(self, location):
        """
        Returns the archive entry in the given location or raises an KeyError,
        if not found
        """
        location = clean_pathname(location)
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
            check_format(format)
        except CombineArchiveFormatException as e:
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


class ArchiveEntry(metadata.MetaDataHolder):
    """
    represents a single entry in a COMBINE archive
    """
    def __init__(self, location, format=None, master=False, zipinfo=None, archive=None):
        super(ArchiveEntry, self).__init__(self)
        self.location = location
        self.format = format
        self.master = master
        self.archive = archive
        self.zipinfo = zipinfo

    def read(self):
        if self.zipinfo is not None and self.archive is not None:
            return self.archive._zip.read( self.zipinfo )
        elif self.zipinfo is None and self.archive is not None:
            return self.archive._zip.read( self.location )
        else:
            raise CombineArchiveException('There is no reference back to the Combine archive')


class CombineArchiveException(Exception):
    pass


class CombineArchiveFormatException(CombineArchiveException):
    pass


def clean_pathname(path):
    """
    basically removes leading slashes, because the python zip does not handle
    them
    """
    path = os.path.normpath(path)
    if path[0] == '/':
        path = path[1:]

    return path


__mime_pattern = re.compile(r'^([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)$')
__purl_mime_base = 'http://purl.org/NET/mediatypes/{ctype}/{format}'
def convert_mimetype(mime):
    """
    dedects and automatically converts mime-type like format specifications
    """
    match = __mime_pattern.match(mime)
    if match:
        # mime is in old mime type format -> put it into purl.org url
        mime = __purl_mime_base.format(ctype=match.group(1), format=match.group(2))

    return mime


__format_url_pattern = re.compile(r'^https?\:\/\/(?:www\.)?(?P<domain>[\w\.\-]+)\/(?P<format>[\w\.\-\/]+)$')
def check_format(format, convert=True):
    """
    checks if either an indentifiers.org format url or a purl.org format url.
    If format uses old mime type schema, it corrects it to use purl.org via
    convert_mimetype()

    Returns:
        format

    Raises CombineArchiveFormatException:
        if format is unknown or not correct
    """
    # first try to fix old mime type declaration, just in case
    if convert:
        format = convert_mimetype(format)

    # check if format is url
    match = __format_url_pattern.match(format)
    if not match:
        # format is not a url
        if convert is False and __mime_pattern.match(format):
            # we're not allowed to change the format, so it could be an mime
            # type
            return format
        else:
            # obviously no url nor mime tpye -> CombineArchiveFormatException
            raise CombineArchiveFormatException('format is not a valid url {}'.format(format))
    else:
        # url schema seems ok -> check for correct base urls (purl.org or
        # identifiers.org)
        domain = match.group('domain')
        if not domain == 'purl.org' and not domain == 'identifiers.org':
            # unknown format domain -> CombineArchiveFormatException
            raise CombineArchiveFormatException('{domain} is an unknown format domain. Just purl.org and identifiers.org are allowed at the moment'.format(domain=domain))

    # everything seems to be alright
    # return format
    return format
