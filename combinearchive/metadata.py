"""
classes representing meta data used in COMBINE Archives, such as the OMEX meta data
"""
import xml.dom.minidom as minidom
from datetime import datetime

import combinearchive as combinearchive


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
        meta.set_about(self, fragment)
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
        description = 'Description'
        about       = 'about'

    class dc_terms:
        description = 'description'
        creator     = 'creator'
        created     = 'created'
        modified    = 'modified'
        w3cdtf      = 'W3CDTF'
        w3cdtf_dateformat = '%Y-%m-%dT%H:%M:%SZ'

    class vcard_terms:
        family_name         = 'family-name'
        given_name          = 'given-name'
        email               = 'email'
        organization_name   = 'organization-name'


class MetaDataObject(object):
    """
    abstract base class for all meta data utilized in COMBINE archives
    """

    def __init__(self, xml_element):
        """ XML element representing the raw meta data"""
        self._xml_element = xml_element
        """ reference to the object, which this meta data is about. Should have the MetaDataHolder mixin"""
        self.about = None
        """ fragment/part of the referenced object, which is described by this meta data"""
        self.fragment = None

        # start parsing
        self._try_parse()

    def set_about(self, about, fragment=None):
        """
        """
        if not isinstance(about, MetaDataHolder):
            raise TypeError('provided about object does not inherit from MetaDataHolder')

        # set according fields
        self.about = about
        self.fragment = fragment

    def _build_desc_elem(self):
        """
        constructs the surrounding rdf:description element and returns it
        useful for _rebuild_xml()
        """
        elem = minidom.createElementNS(Namespace.RDF_URI, Namespace.rdf_terms.description)
        if isinstance(combinearchive.CombineArchive, self.about):
            # meta data is about the archive itself
            about_url = '.'
        elif isinstance(combinearchive.ArchiveEntry, self.about):
            # meta data is about a normal archive entry
            about_url = self.about.location

        # add fragment
        if self.fragment:
            about_url = '{loc}#{frag}'.format(loc=about_url, frag=self.fragment)

        elem.setAttributeNS(Namespace.RDF_URI, Namespace.rdf_terms.about, about_url)
        return elem

    def _try_parse(self):
        """
        tries to parse the meta data encoded in _xml_element
        """
        raise NotImplemented()

    def _rebuild_xml(self):
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
        super(DefaultMetaDataObject, self).__init__(self, xml_element)

    def _try_parse(self):
        return self

    def _rebuild_xml(self):
        return self._xml_element


class OmexMetaDataObject(MetaDataObject):
    """
    Object representing the meta data described in the original
    COMBINE Archive specification
    """

    def __init__(self, xml_element):
        super(OmexMetaDataObject, self).__init__(self, xml_element)

        self.created = datetime.now()
        self.creator = list()
        self.modified = list()
        self.description = None

    def _try_parse(self):
        try:
            # getting the dcterms description
            desc_elems = self._xml_element.getElementsByTagNameNS(Namespace.DC_URI, Namespace.dc_terms.description)
            if len(desc_elems) > 0:
                # self.description = __get_text_from_elem(desc_elems[0])
                # just format as xml, in case there are any HTML tag included
                self.description = desc_elems[0].toxml()

            # parsing the date of creation
            created_elems = self._xml_element.getElementsByTagNameNS(Namespace.DC_URI, Namespace.dc_terms.created)
            if len(created_elems) > 0:
                date_str = __get_text_from_elem(created_elems.getElementsByTagNameNS(Namespace.DC_URI, Namespace.dc_terms.w3cdtf)[0])
                self.created = self._parse_date(date_str)

            # parsing the creator VCard
            creator_elems = self._xml_element.getElementsByTagNameNS(Namespace.DC_URI, Namespace.dc_terms.creator)
            for creator in creator_elems:
                self.creator.append( VCard.parse_xml(creator) )

            # parsing all modification dates with nested W3CDFT date declaration
            modified_elems = self._xml_element.getElementsByTagNameNS(Namespace.DC_URI, Namespace.dc_terms.modified)
            for mod in modified_elems:
                date_str = __get_text_from_elem(mod.getElementsByTagNameNS(Namespace.DC_URI, Namespace.dc_terms.w3cdtf))
                self.modified.append( self._parse_date(date_str) )

        except BaseException as e :
            raise ValueError('an error occured, while parsing omex meta data {}'.format(e.message))
        else:
            return self

    def _rebuild_xml(self):
        # TODO
        # builds top-level rdf:Description element
        elem = self._build_desc_elem()

        # add description
        desc_elem = elem.createElementNS(Namespace.VCARD_URI, Namespace.dc_terms.description)
        desc_elem.appendChild( elem.createTextNode(self.description) )
        elem.appendChild(desc_elem)

        # add date of creation
        created_elem = elem.createElementNS(Namespace.DC_URI, Namespace.dc_terms.created)
        w3cdtf_elem = elem.createElementNS(Namespace.DC_URI, Namespace.dc_terms.w3cdtf)
        w3cdtf_elem.appendChild( elem.createTextNode(self.created.strftime(Namespace.dc_terms.w3cdtf_dateformat)) )
        created_elem.appendChild(w3cdtf_elem)
        elem.appendChild(created_elem)

        # add all modification dates
        for mod_date in self.modified:
            modified_elem = elem.createElementNS(Namespace.DC_URI, Namespace.dc_terms.modified)
            w3cdtf_elem = elem.createElementNS(Namespace.DC_URI, Namespace.dc_terms.w3cdtf)
            w3cdtf_elem.appendChild( elem.createTextNode(mod_date.strftime(Namespace.dc_terms.w3cdtf_dateformat)) )
            modified_elem.appendChild(w3cdtf_elem)
            elem.appendChild(modified_elem)

        # add all VCards
        for vcard in self.creator:
            creator_elem = vcard.build_xml()
            elem.appendChild(creator_elem)

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
        fn_elems = xml_element.getElementsByTagNameNS(Namespace.VCARD_URI, Namespace.vcard_terms.family_name)
        if len(fn_elems) > 0:
            vcard.family_name = __get_text_from_elem(fn_elems[0])

        # parse given name
        gn_elems = xml_element.getElementsByTagNameNS(Namespace.VCARD_URI, Namespace.vcard_terms.given_name)
        if len(gn_elems) > 0:
            vcard.given_name = __get_text_from_elem(gn_elems[0])

        # parse email
        em_elems = xml_element.getElementsByTagNameNS(Namespace.VCARD_URI, Namespace.vcard_terms.email)
        if len(em_elems) > 0:
            vcard.email = __get_text_from_elem(em_elems[0])

        # parse organization name
        on_elems = xml_element.getElementsByTagNameNS(Namespace.VCARD_URI, Namespace.vcard_terms.organization_name)
        if len(on_elems) > 0:
            vcard.organization = __get_text_from_elem(on_elems[0])

        # return parsed object
        return vcard

    def build_xml(self):
        # generate new xml element
        # (vcards are always housed in a dcterms:creator elem)
        elem = minidom.createElementNS(Namespace.DC_URI, Namespace.dc_terms.creator)

        # add family name
        fn_elem = elem.createElementNS(Namespace.VCARD_URI, Namespace.vcard_terms.family_name)
        fn_elem.appendChild(elem.createTextNode(self.family_name))
        elem.appendChild(fn_elem)

        # add given name
        gn_elem = elem.createElementNS(Namespace.VCARD_URI, Namespace.vcard_terms.given_name)
        gn_elem.appendChild(elem.createTextNode(self.given_name))
        elem.appendChild(gn_elem)

        # add email
        em_elem = elem.createElementNS(Namespace.VCARD_URI, Namespace.vcard_terms.email)
        em_elem.appendChild(elem.createTextNode(self.email))
        elem.appendChild(em_elem)

        # add oragnization
        on_elem = elem.createElementNS(Namespace.VCARD_URI, Namespace.vcard_terms.organization_name)
        on_elem.appendChild(elem.createTextNode(self.organization))
        elem.appendChild(on_elem)

        return elem


def __get_text_from_elem(xml_element):
    """
    gets all textNodes under the given element as String
    """
    return ' '.join(t.nodeValue for t in xml_element.childNodes if t.nodeType == t.TEXT_NODE)
