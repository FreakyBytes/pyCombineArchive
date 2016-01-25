from zipfile import ZipFile
import xml.dom.minidom as minidom


class CombineArchive:
    MANIFEST_LOCATION = 'manifest.xml'
    METADATA_LOCATION = 'metadata.rdf'

    _XML_ROOT_ELEM = 'omexManifest'
    _XML_ROOT_NS = 'http://identifiers.org/combine.specifications/omex-manifest'
    _XML_CONTENT_TAG = 'content'
    _XML_CONTENT_LOCATION = 'location'
    _XML_CONTENT_FORMAT = 'format'
    _XML_CONTENT_MASTER = 'master'

    def __init__(self, archive):
        self._archive = archive
        self._zip = ZipFile(archive, 'a')
        self.entries = dict()

        self._read_manifest()
        self._read_metadata()

    def __exit__(self):
        self.close()

    def _read_manifest(self):
        """
        internal function.
        Reads the manifest file of a CombineArchive
        """
        with self._zip.open(self.MANIFEST_LOCATION) as manifest_file:
            manifest = minidom.parseString( manifest_file.readlines() )

        # check for correct root element and namespace
        root = manifest.documentElement
        if root.tagName != self._XML_ROOT_ELEM or root.getAttribute('xmlns') != self._XML_ROOT_NS:
            raise CombineArchiveException('manifest has no valid omex root element')

        # check entries
        for entry in root.getElementsByTagName(self._XML_CONTENT_TAG):
            location = entry.getAttribute(self._XML_CONTENT_LOCATION)
            format = entry.getAttribute(self._XML_CONTENT_FORMAT)
            master = (True if entry.getAttribute(self._XML_CONTETN_MASTER) == 'True' else False)

            if not location or not format:
                raise CombineArchiveException('location and format field are required. Corrupt manifest.xml')

            # check if file is in zip
            try:
                self._zip.getinfo(location)
            except KeyError:
                raise CombineArchiveException("{location} is specified by the manifest, but not contained by the ZIP file".format(location=location))

            archive_entry = ArchiveEntry(location, format=format, master=master)
            self.entries[location] = archive_entry

    def _read_metadata(self):
        pass

    def _write_manifest(self):
        pass

    def _write_metadata(self):
        pass

    def close(self):
        pass

    def pack(self):
        pass

    def add_entry(self, filename, location=None, main_entry=False):
        pass

    def remove_entry(self, location):
        pass

    def get_entry(self, location):
        pass


class ArchiveEntry:

    def __init__(self, location, format=None, master=False, archive=None):
        self.location = location
        self.format = format
        self.master = master
        self.archive = archive


class CombineArchiveException(Exception):
    pass
