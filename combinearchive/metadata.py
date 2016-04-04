"""
classes representing meta data used in COMBINE Archives, such as the OMEX meta data
"""
from datetime import datetime
from xml.etree import ElementTree
try:
    # Python 3
    from urllib.parse import urlparse, urljoin
except ImportError:
    # Python 2
    from urlparse import urlparse, urljoin

import combinearchive as combinearchive
import utils
import exceptions


def _get_text_from_elem(xml_element):
    """
    gets all textNodes under the given element as String
    """
    return ' '.join(t.nodeValue for t in xml_element.childNodes if t.nodeType == t.TEXT_NODE)


class MetaDataHolder(object):
    """
    Mixin for objects, which can contain/be described by meta data
    """

    def __init__(self):
        self.description = list()

    def add_description(self, meta, fragment=None):
        """
        adds a description to this meta data holder.
        Optionally you can define a fragment to specify the part, which is described
        by the MetaDataObject.
        """
        if not meta:
            # Error no meta data provided
            raise ValueError('no meta data was provided to be added')
        if not isinstance(meta, MetaDataObject):
            # wrong class
            raise TypeError('provided meta data does not inherit from MetaDataObject')

        # set information to MetaDataObject
        meta.set_about(self, fragment=fragment)
        # add it to the list
        self.description.append(meta)


class Namespace(object):
    """
    class holding constants for the XML namespaces
    """
    DC          = 'dcterms'
    DC_URI      = 'http://purl.org/dc/terms/'
    VCARD       = 'vCard'
    VCARD_URI   = 'http://www.w3.org/2006/vcard/ns#'
    BQMODEL     = 'bqmodel'
    BQMODEL_URI = 'http://biomodels.net/model-qualifiers/'
    RDF         = 'rdf'
    RDF_URI     = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

    class rdf_terms:
        rdf         = 'rdf:RDF'
        description = 'rdf:Description'
        about       = 'rdf:about'
        parse_type  = 'rdf:parseType'
        bag         = 'rdf:Bag'
        li          = 'rdf:li'

    class dc_terms:
        description = 'dcterms:description'
        creator     = 'dcterms:creator'
        created     = 'dcterms:created'
        modified    = 'dcterms:modified'
        w3cdtf      = 'dcterms:W3CDTF'
        w3cdtf_dateformat = '%Y-%m-%dT%H:%M:%SZ'

    class vcard_terms:
        has_name            = 'vCard:hasName'
        family_name         = 'vCard:family-name'
        given_name          = 'vCard:given-name'
        email               = 'vCard:email'
        organization_name   = 'vCard:organization-name'


class MetaDataObject(object):
    """
    abstract base class for all meta data utilized in COMBINE archives
    """

    def __init__(self, xml_element=None):
        """ XML element representing the raw meta data"""
        self._xml_element = xml_element
        """ reference to the object, which this meta data is about. Should have the MetaDataHolder mixin"""
        self.about = None
        """ fragment/part of the referenced object, which is described by this meta data"""
        self.fragment = None

        if xml_element is not None:
            # start parsing
            self._try_parse()

    def set_about(self, about, fragment=None, add_to_target=False):
        """
        """
        if about is None:
            raise ValueError('about is not supposed to be None')

        if not isinstance(about, MetaDataHolder):
            raise TypeError('provided about object does not inherit from MetaDataHolder')

        # set according fields
        self.about = about
        self.fragment = fragment

        # auto wire, if wished
        if add_to_target:
            self.about.add_description(self, fragment=None)

    def _build_desc_elem(self):
        """
        constructs the surrounding rdf:description element and returns it
        useful for _rebuild_xml()
        """
        elem = ElementTree.Element(utils.extend_tag_name(Namespace.rdf_terms.description, combinearchive._XML_NS))
        if isinstance(self.about, combinearchive.CombineArchive):
            # meta data is about the archive itself
            about_url = '.'
        elif isinstance(self.about, combinearchive.ArchiveEntry):
            # meta data is about a normal archive entry
            about_url = self.about.location

        # add fragment
        if self.fragment:
            about_url = urljoin(about_url, '#{}'.format(self.fragment))

        elem.attrib[utils.extend_tag_name(Namespace.rdf_terms.about, combinearchive._XML_NS)] = about_url
        return elem

    def _try_parse(self):
        """
        tries to parse the meta data encoded in _xml_element
        """
        raise NotImplemented()

    def _rebuild_xml(self, document):
        """
        rebuilds the xml element so it can be stored again into the RDF file

        Returns:
            the xml_element
        """
        raise NotImplemented()


class DefaultMetaDataObject(MetaDataObject):
    """
    default class for meta data in a COMBINE archive
    just plain representation of the XML element
    """

    def __init__(self, xml_element):
        super(DefaultMetaDataObject, self).__init__(xml_element)

    def _try_parse(self):
        return self

    def _rebuild_xml(self, document):
        return self._xml_element


class OmexMetaDataObject(MetaDataObject):
    """
    Object representing the meta data described in the original
    COMBINE Archive specification
    """

    def __init__(self, xml_element=None):

        self.created = datetime.now()
        self.creator = list()
        self.modified = list()
        self.description = None

        super(OmexMetaDataObject, self).__init__(xml_element=xml_element)

    def _try_parse(self):
        try:
            # getting the dcterms description
            desc_elem = self._xml_element.find(Namespace.dc_terms.description, combinearchive._XML_NS)
            if desc_elem:
                self.description = desc_elem.text

            # parsing the date of creation
            created_elem = self._xml_element.find(Namespace.dc_terms.created, combinearchive._XML_NS)
            if created_elem:
                w3cdtf = created_elem.find(Namespace.dc_terms.w3cdtf, combinearchive._XML_NS)
                self.created = self._parse_date(w3cdtf.text)

            # parsing the creator VCard
            creator_elems = self._xml_element.findall(Namespace.dc_terms.creator, combinearchive._XML_NS)
            for creator in creator_elems:
                self.creator.append(VCard.parse_xml(creator))

            # parsing all modification dates with nested W3CDFT date declaration
            modified_elems = self._xml_element.findall(Namespace.dc_terms.modified, combinearchive._XML_NS)
            for mod in modified_elems:
                w3cdtf = modified_elems.find(Namespace.dc_terms.w3cdtf, combinearchive._XML_NS)
                self.modified.append(self._parse_date(w3cdtf.text))

        except BaseException as e:
            raise ValueError('an error occurred, while parsing omex meta data {}'.format(e.message))
        else:
            return self

    def _rebuild_xml(self):
        # TODO
        # builds top-level rdf:Description element
        elem = self._build_desc_elem()

        # add description
        if self.description and self.description != '':
            desc_elem = ElementTree.SubElement(elem, utils.extend_tag_name(Namespace.dc_terms.description, combinearchive._XML_NS))
            desc_elem.text = self.description

        # add date of creation
        if self.created:
            created_elem = ElementTree.SubElement(elem, utils.extend_tag_name(Namespace.dc_terms.created, combinearchive._XML_NS))
            w3cdtf = ElementTree.SubElement(created_elem, utils.extend_tag_name(Namespace.dc_terms.w3cdtf, combinearchive._XML_NS))
            w3cdtf.text = self.created.strftime(Namespace.dc_terms.w3cdtf_dateformat)

        # add all modification dates
        for mod_date in self.modified:
            modified_elem = ElementTree.SubElement(elem, utils.extend_tag_name(Namespace.dc_terms.modified, combinearchive._XML_NS))
            w3cdtf = ElementTree.SubElement(modified_elem, utils.extend_tag_name(Namespace.dc_terms.w3cdtf, combinearchive._XML_NS))
            w3cdtf.text = mod_date.strftime(Namespace.dc_terms.w3cdtf_dateformat)

        # add all VCards
        for vcard in self.creator:
            creator_elem = vcard.build_xml()
            elem.append(creator_elem)

        self._xml_element = elem
        return self._xml_element

    def _parse_date(self, str_datetime):
        """
        parses the W3CDTF time format

        Returns:
            datetime object

        Raises ValueError:
            in case the date cannot be parsed

        """
        return datetime.strptime(str_datetime, Namespace.dc_terms.w3cdtf_dateformat)


class VCard(object):

    def __init__(self, family_name=None, given_name=None, email=None, organization=None):
        self.family_name    = family_name
        self.given_name     = given_name
        self.email          = email
        self.organization   = organization

    @staticmethod
    def parse_xml(xml_element):
        # generate new VCard object
        vcard = VCard()

        # parse family name
        fn_elem = xml_element.find(Namespace.vcard_terms.family_name, combinearchive._XML_NS)
        if fn_elem:
            vcard.family_name = fn_elem.text

        # parse given name
        gn_elem = xml_element.find(Namespace.vcard_terms.given_name, combinearchive._XML_NS)
        if gn_elem:
            vcard.given_name = gn_elem.text

        # parse email
        em_elem = xml_element.find(Namespace.vcard_terms.email, combinearchive._XML_NS)
        if em_elem:
            vcard.email = em_elem.text

        # parse organization name
        on_elem = xml_element.find(Namespace.vcard_terms.organization_name, combinearchive._XML_NS)
        if on_elem:
            vcard.organization = on_elem.text

        # return parsed object
        return vcard

    def build_xml(self):
        # generate new xml element
        # (vcards are always housed in a dcterms:creator elem)
        elem = ElementTree.Element(utils.extend_tag_name(Namespace.dc_terms.creator, combinearchive._XML_NS))
        elem.attrib[utils.extend_tag_name(Namespace.rdf_terms.parse_type, combinearchive._XML_NS)] = 'Resource'

        # name tag
        if (self.family_name and self.family_name != '') or (self.given_name and self.given_name != ''):
            hasname_elem = ElementTree.SubElement(elem, utils.extend_tag_name(Namespace.vcard_terms.has_name, combinearchive._XML_NS))
            hasname_elem.attrib[utils.extend_tag_name(Namespace.rdf_terms.parse_type, combinearchive._XML_NS)] = 'Resource'

            # add family name
            if self.family_name and self.family_name != '':
                fn_elem = ElementTree.SubElement(hasname_elem, utils.extend_tag_name(Namespace.vcard_terms.family_name, combinearchive._XML_NS))
                fn_elem.text = self.family_name

            # add given name
            if self.given_name and self.given_name != '':
                gn_elem = ElementTree.SubElement(hasname_elem, utils.extend_tag_name(Namespace.vcard_terms.given_name, combinearchive._XML_NS))
                gn_elem.text = self.given_name

        # add email
        if self.email and self.email != '':
            em_elem = ElementTree.SubElement(elem, utils.extend_tag_name(Namespace.vcard_terms.email, combinearchive._XML_NS))
            em_elem.text = self.email

        # add organization
        if self.organization and self.organization != '':
            on_elem = ElementTree.SubElement(elem, utils.extend_tag_name(Namespace.vcard_terms.email, combinearchive._XML_NS))
            on_elem.text = self.organization

        return elem