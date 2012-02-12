# -*- coding: utf-8 -*-
"""
    sleekxmpp.xmlstream.ssl_socket
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The intent of the ssl_socket module is to provide
    SSL certificate validation using PyOpenSSL and
    pyasn1. However, these libraries are "optional"
    if you do not care to validate certs, and are
    ok with the cert checking done by Python's 
    standard library.

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

import ssl
import logging


log = logging.getLogger(__name__)

PYOPENSSL_SUPPORT = False

try:
    import OpenSSL
    import OpenSSL.crypto
    import OpenSSL.SSL

    from pyasn1.type import univ, char, tag, constraint
    from pyasn1.type.namedtype import NamedType, NamedTypes
    from pyasn1.type.constraint import ValueSizeConstraint
    from pyasn1.codec.der.decoder import decode


    PYOPENSSL_SUPPORT = True


    XMPPADDR_OIDS = ['1.3.6.1.5.5.7.8.5', 
                     'urn:oid:1.3.6.1.5.5.7.8.5',
                     'id-on-xmppAddr']

    DNSSRV_OIDS = ['1.3.6.1.5.5.7.8.7',
                   'urn:oid:1.3.6.1.5.5.7.8.7',
                   'id-on-dnsSRV']


    # =====================================================================
    # Setup classes for pyasn1 parsing

    MAX = 64
    CONSTRAINT = {'subtypeSpec': ValueSizeConstraint(1, MAX)}

    class DirectoryString(univ.Choice):
        componentType = NamedTypes(
                NamedType('teletexString',
                    char.TeletexString().subtype(**CONSTRAINT)),
                NamedType('printableString', 
                    char.PrintableString().subtype(**CONSTRAINT)),
                NamedType('universalString',
                    char.UniversalString().subtype(**CONSTRAINT)),
                NamedType('utf8String', 
                    char.UTF8String().subtype(**CONSTRAINT)),
                NamedType('bmpString',
                    char.BMPString().subtype(**CONSTRAINT)),
                NamedType('ia5String',
                    char.IA5String().subtype(**CONSTRAINT)),
                NamedType('gString',
                    univ.OctetString().subtype(**CONSTRAINT)))


    class AttributeValue(DirectoryString):
        pass


    class AttributeType(univ.ObjectIdentifier):
        pass


    class AttributeTypeAndValue(univ.Sequence):
        componentType = NamedTypes(
            NamedType('type', AttributeType()),
            NamedType('value', AttributeValue()))


    class RelativeDistinguishedName(univ.SetOf):
        componentType = AttributeTypeAndValue()


    class RDNSequence(univ.SequenceOf):
        componentType = RelativeDistinguishedName()


    class Name(univ.Choice):
        componentType = NamedTypes(NamedType('', RDNSequence()))


    class GeneralName(univ.Choice):
        componentType = NamedTypes(
                NamedType('otherName',
                    univ.Sequence().subtype(
                        implicitTag=tag.Tag(
                            tag.tagClassContext,
                            tag.tagFormatConstructed,
                            0))),
                NamedType('rfc822Name',
                    char.IA5String().subtype(
                        implicitTag=tag.Tag(
                            tag.tagClassContext,
                            tag.tagFormatSimple,
                            1))),
                NamedType('dNSName',
                    char.IA5String().subtype(
                        implicitTag=tag.Tag(
                            tag.tagClassContext,
                            tag.tagFormatSimple,
                            2))),
                NamedType('x400Address',
                    univ.Sequence().subtype(
                        implicitTag=tag.Tag(
                            tag.tagClassContext,
                            tag.tagFormatConstructed,
                            3))),
                NamedType('directoryName',
                    Name().subtype(
                        implicitTag=tag.Tag(
                            tag.tagClassContext,
                            tag.tagFormatConstructed,
                            4))),
                NamedType('ediPartyName',
                    univ.Sequence().subtype(
                        implicitTag=tag.Tag(
                            tag.tagClassContext,
                            tag.tagFormatConstructed,
                            5))),
                NamedType('uniformResourceIdentifier',
                    char.IA5String().subtype(
                        implicitTag=tag.Tag(
                            tag.tagClassContext,
                            tag.tagFormatSimple,
                            6))),
                NamedType('iPAddress',
                    univ.OctetString().subtype(
                        implicitTag=tag.Tag(
                            tag.tagClassContext,
                            tag.tagFormatSimple,
                            7))),
                NamedType('registeredID',
                    univ.ObjectIdentifier().subtype(
                        implicitTag=tag.Tag(
                            tag.tagClassContext,
                            tag.tagFormatSimple,
                            8))))

    class GeneralNames(univ.SequenceOf):
        componentType = GeneralName()
        sizeSpec = univ.SequenceOf.sizeSpec + \
                   constraint.ValueSizeConstraint(1, MAX)

except ImportError:
    PYOPENSSL_SUPPORT = False


# =====================================================================


def extract_xmpp_addresses(cert):
    if PYOPENSSL_SUPPORT:
        pass
    else:
        return {}

def check_certificate(cert, domain):
    if PYOPENSSL_SUPPORT:
        pass
    else:
        pass

def wrap(socket, context=None):
    if PYOPENSSL_SUPPORT:
        socket = OpenSSL.SSL.Connection(context, socket)
        socket.set_connect_state()
        return socket
    else:
        log.warning("PyOpenSSL/pyasn1 not found, using built-in" + \
                    " SSL module")
        if not context.ca_certs:
            cert_policy = ssl.CERT_NONE
            log.warning("Server certificate will NOT be validated!")
        else:
            cert_policy = ssl.CERT_REQUIRED
            log.warning("Certificate validation will not be sufficient" + \
                        " for security conscious applications.")

        return ssl.wrap_socket(socket, 
                               ssl_version=context.ssl_version,
                               do_handshake_on_connect=False,
                               ca_certs=context.ca_certs,
                               cert_reqs=cert_policy)
