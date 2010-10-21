"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from __future__ import unicode_literals
import types


def tostring(xml=None, xmlns='', stanza_ns='', stream=None, outbuffer=''):
    """
    Serialize an XML object to a Unicode string.

    If namespaces are provided using xmlns or stanza_ns, then elements
    that use those namespaces will not include the xmlns attribute in
    the output.

    Arguments:
        xml       -- The XML object to serialize. If the value is None,
                     then the XML object contained in this stanza
                     object will be used.
        xmlns     -- Optional namespace of an element wrapping the XML
                     object.
        stanza_ns -- The namespace of the stanza object that contains
                     the XML object.
        stream    -- The XML stream that generated the XML object.
        outbuffer -- Optional buffer for storing serializations during
                     recursive calls.
    """
    # Add previous results to the start of the output.
    output = [outbuffer]

    # Extract the element's tag name.
    tag_name = xml.tag.split('}', 1)[-1]

    # Extract the element's namespace if it is defined.
    if '}' in xml.tag:
        tag_xmlns = xml.tag.split('}', 1)[0][1:]
    else:
        tag_xmlns = u''

    # Output the tag name and derived namespace of the element.
    namespace = u''
    if tag_xmlns not in ['', xmlns, stanza_ns]:
        namespace = u' xmlns="%s"' % tag_xmlns
        if stream and tag_xmlns in stream.namespace_map:
            mapped_namespace = stream.namespace_map[tag_xmlns]
            if mapped_namespace:
                tag_name = u"%s:%s" % (mapped_namespace, tag_name)
    output.append(u"<%s" % tag_name)
    output.append(namespace)

    # Output escaped attribute values.
    for attrib, value in xml.attrib.items():
        if '{' not in attrib:
            value = xml_escape(value)
            output.append(u' %s="%s"' % (attrib, value))

    if len(xml) or xml.text:
        # If there are additional child elements to serialize.
        output.append(u">")
        if xml.text:
            output.append(xml_escape(xml.text))
        if len(xml):
            for child in xml.getchildren():
                output.append(tostring(child, tag_xmlns, stanza_ns, stream))
        output.append(u"</%s>" % tag_name)
    elif xml.text:
        # If we only have text content.
        output.append(u">%s</%s>" % (xml_escape(xml.text), tag_name))
    else:
        # Empty element.
        output.append(u" />")
    if xml.tail:
        # If there is additional text after the element.
        output.append(xml_escape(xml.tail))
    return u''.join(output)


def xml_escape(text):
    """
    Convert special characters in XML to escape sequences.

    Arguments:
        text -- The XML text to convert.
    """
    if type(text) != types.UnicodeType:
        text = list(unicode(text, 'utf-8', 'ignore'))
    else:
        text = list(text)
    escapes = {u'&': u'&amp;',
               u'<': u'&lt;',
               u'>': u'&gt;',
               u"'": u'&apos;',
               u'"': u'&quot;'}
    for i, c in enumerate(text):
        text[i] = escapes.get(c, c)
    return u''.join(text)
