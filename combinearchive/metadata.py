"""
classes representing meta data used in COMBINE Archives, such as the OMEX meta data
"""


class MetaDataHolder:
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


class MetaDataObject:
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

    def _try_parse(self):
        """
        tries to parse the meta data encoded in _xml_element
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
        pass


class OmexMetaDataObject(MetaDataObject):
    """
    Object representing the meta data described in the original
    COMBINE Archive specification
    """

    def __init__(self, xml_element):
        super(OmexMetaDataObject, self).__init__(self, xml_element)

        self.created = None
        self.creator = list()
        self.modified = list()
        self.description = None

    def _try_parse(self):
        # TODO
        pass
