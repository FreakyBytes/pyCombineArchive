import re
import os
# from xml.etree import ElementTree
import exceptions

# regex
__xml_tag_regex = re.compile(r'^(?:(?P<prefix>[\w]+):)?(?P<tag>[\w]+)$')
__mime_pattern = re.compile(r'^([a-zA-Z0-9\+]+)/([a-zA-Z0-9\+]+)$')
__purl_mime_base = 'http://purl.org/NET/mediatypes/{ctype}/{format}'
__format_url_pattern = re.compile(r'^https?\:\/\/(?:www\.)?(?P<domain>[\w\.\-]+)\/(?P<format>[\w\.\-+\/]+)$')


def extend_tag_name(tag_name, namespace_dict):
    """
    expands the short form of namespace tag notation to the full form.
    eg. '{rdf}:Description -> '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}:Description'

    :param tag_name:
    :param namespace_dict:
    :return:
    """
    match = __xml_tag_regex.match(tag_name)
    if match:
        return '{{{ns}}}:{tag}'.format(ns=namespace_dict[match.group('prefix')], tag=match.group('tag'))
    else:
        return tag_name


def get_attribute(element, attr_name, namespace_dict):
    """
    Tries to find an attribute with given name in the element.
    Looks first for an attribute with namespace notation. If this fails it tries again, but without any namespace

    :param element:
    :param attr_name:
    :param namespace_dict:
    :return:
    :raises KeyError: if attribute not found
    """
    try:
        # try to find attr with ns
        return element.attrib[extend_tag_name(attr_name, namespace_dict)]
    except KeyError:
        # remove ns and try again
        match = __xml_tag_regex.match(attr_name)
        return element.attrib[match.group('tag')]


def clean_pathname(path):
    """
    basically removes leading slashes, because the python zip does not handle
    them
    """
    path = os.path.normpath(unicode(path))
    if path[0] == '/':
        path = path[1:]

    return path


def convert_mimetype(mime):
    """
    dedects and automatically converts mime-type like format specifications
    """
    match = __mime_pattern.match(mime)
    if match:
        # mime is in old mime type format -> put it into purl.org url
        mime = __purl_mime_base.format(ctype=match.group(1), format=match.group(2))

    return mime


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
            raise exceptions.CombineArchiveFormatException('format is not a valid url {}'.format(format))
    else:
        # url schema seems ok -> check for correct base urls (purl.org or
        # identifiers.org)
        domain = match.group('domain')
        if not domain == 'purl.org' and not domain == 'identifiers.org':
            # unknown format domain -> CombineArchiveFormatException
            raise exceptions.CombineArchiveFormatException('{domain} is an unknown format domain. Just purl.org and identifiers.org are allowed at the moment'.format(domain=domain))

    # everything seems to be alright
    # return format
    return format
