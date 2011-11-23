.. module:: sleekxmpp.xmlstream.tostring

.. _tostring:

XML Serialization
=================

Since the XML layer of SleekXMPP is based on :mod:`~xml.etree.ElementTree`,
why not just use the built-in :func:`~xml.etree.ElementTree.tostring`
method? The answer is that using that method produces ugly results when
using namespaces. The :func:`tostring()` method used here intelligently
hides namespaces when able and does not introduce excessive namespace
prefixes::

    >>> from sleekxmpp.xmlstream.tostring import tostring
    >>> from xml.etree import cElementTree as ET
    >>> xml = ET.fromstring('<foo xmlns="bar"><baz /></foo>')
    >>> ET.tostring(xml)
    '<ns0:foo xmlns:ns0="bar"><ns0:baz /></foo>'
    >>> tostring(xml)
    '<foo xmlns="bar"><baz /></foo>'

As a side effect of this namespace hiding, using :func:`tostring()` may
produce unexpected results depending on how the :func:`tostring()` method
is invoked. For example, when sending XML on the wire, the main XMPP
stanzas with their namespace of ``jabber:client`` will not include the
namespace because that is already declared by the stream header. But, if
you create a :class:`~sleekxmpp.stanza.message.Message` instance and dump
it to the terminal, the ``jabber:client`` namespace will appear.

.. autofunction:: tostring

Escaping Special Characters
---------------------------

In order to prevent errors when sending arbitrary text as the textual
content of an XML element, certain characters must be escaped. These
are: ``&``, ``<``, ``>``, ``"``, and ``'``. The default escaping
mechanism is to replace those characters with their equivalent escape
entities: ``&amp;``, ``&lt;``, ``&gt;``, ``&apos;``, and ``&quot;``.

In the future, the use of CDATA sections may be allowed to reduce the
size of escaped text or for when other XMPP processing agents do not
undertand these entities.

.. autofunction:: xml_escape
