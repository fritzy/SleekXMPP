# -*- coding: utf-8 -*-
"""
    sleekxmpp.jid
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module allows for working with Jabber IDs (JIDs) by
    providing accessors for the various components of a JID.

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

from __future__ import unicode_literals

import re
import socket
import stringprep
import encodings.idna

from sleekxmpp.util import stringprep_profiles


ILLEGAL_CHARS = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r' + \
                '\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19' + \
                '\x1a\x1b\x1c\x1d\x1e\x1f' + \
                ' !"#$%&\'()*+,./:;<=>?@[\\]^_`{|}~\x7f'

JID_PATTERN = "^(?:([^\"&'/:<>@]{1,1023})@)?([^/@]{1,1023})(?:/(.{1,1023}))?$"


nodeprep = stringprep_profiles.create(
    nfkc=True,
    bidi=True,
    mappings=[
        stringprep_profiles.b1_mapping,
        stringprep_profiles.c12_mapping],
    prohibited=[
        stringprep.in_table_c11,
        stringprep.in_table_c12,
        stringprep.in_table_c21,
        stringprep.in_table_c22,
        stringprep.in_table_c3,
        stringprep.in_table_c4,
        stringprep.in_table_c5,
        stringprep.in_table_c6,
        stringprep.in_table_c7,
        stringprep.in_table_c8,
        stringprep.in_table_c9,
        lambda c: c in '\'"&/:<>@'],
    unassigned=[stringprep.in_table_a1])


resourceprep = stringprep_profiles.create(
    nfkc=True,
    bidi=True,
    mappings=[stringprep_profiles.b1_mapping],
    prohibited=[
        stringprep.in_table_c12,
        stringprep.in_table_c21,
        stringprep.in_table_c22,
        stringprep.in_table_c3,
        stringprep.in_table_c4,
        stringprep.in_table_c5,
        stringprep.in_table_c6,
        stringprep.in_table_c7,
        stringprep.in_table_c8,
        stringprep.in_table_c9],
    unassigned=[stringprep.in_table_a1])


class InvalidJID(ValueError):
    pass


def parse_jid(data):
    """
    Parse string data into the node, domain, and resource
    components of a JID.
    """
    match = re.match(JID_PATTERN, data)
    if not match:
        raise InvalidJID

    (node, domain, resource) = match.groups()

    ip_addr = False

    try:
        socket.inet_aton(domain)
        ip_addr = True
    except socket.error:
        pass

    if not ip_addr and hasattr(socket, 'inet_pton'):
        try:
            socket.inet_pton(socket.AF_INET6, domain.strip('[]'))
            ip_addr = True
        except socket.error:
            pass

    if not ip_addr:
        domain_parts = []
        for label in domain.split('.'):
            try:
                label = encodings.idna.nameprep(label)
                encodings.idna.ToASCII(label)
            except UnicodeError:
                raise InvalidJID

            for char in label:
                if char in ILLEGAL_CHARS:
                    raise InvalidJID

            if '-' in (label[0], label[-1]):
                raise InvalidJID

            domain_parts.append(label)
        domain = '.'.join(domain_parts)

    try:
        if node is not None:
            node = nodeprep(node)
        if resource is not None:
            resource = resourceprep(resource)
    except stringprep_profiles.StringPrepError:
        raise InvalidJID

    return node, domain, resource


class JID(object):

    """
    A representation of a Jabber ID, or JID.

    Each JID may have three components: a user, a domain, and an optional
    resource. For example: user@domain/resource

    When a resource is not used, the JID is called a bare JID.
    The JID is a full JID otherwise.

    **JID Properties:**
        :jid: Alias for ``full``.
        :full: The string value of the full JID.
        :bare: The string value of the bare JID.
        :user: The username portion of the JID.
        :username: Alias for ``user``.
        :local: Alias for ``user``.
        :node: Alias for ``user``.
        :domain: The domain name portion of the JID.
        :server: Alias for ``domain``.
        :host: Alias for ``domain``.
        :resource: The resource portion of the JID.

    :param string jid: A string of the form ``'[user@]domain[/resource]'``.
    """

    def __init__(self, jid=None, local=None, domain=None, resource=None):
        """Initialize a new JID"""
        self._jid = (None, None, None)

        if jid is None or jid == '':
            jid = (None, None, None)
        elif not isinstance(jid, JID):
            jid = parse_jid(jid)
        else:
            jid = jid._jid

        orig_local, orig_domain, orig_resource = jid
        self._jid = (local or orig_local or None,
                     domain or orig_domain or None,
                     resource or orig_resource or None)

    def regenerate(self):
        """Deprecated"""
        pass

    def reset(self, data):
        """Start fresh from a new JID string.

        :param string data: A string of the form ``'[user@]domain[/resource]'``.
        """
        self._jid = JID(data)._jid

    def __getattr__(self, name):
        """handle getting the jid values, using cache if available.

        :param name: one of: user, server, domain, resource,
                     full, or bare.
        """
        if name == 'resource':
            return self._jid[2] or ''
        elif name in ('user', 'username', 'local', 'node'):
            return self._jid[0] or ''
        elif name in ('server', 'domain', 'host'):
            return self._jid[1] or ''
        elif name in ('full', 'jid'):
            return str(self)
        elif name == 'bare':
            return str(JID(local=self._jid[0],
                           domain=self._jid[1]))
        else:
            object.__getattr__(self, name)

    def __setattr__(self, name, value):
        """handle getting the jid values, using cache if available.

        :param name: one of: ``user``, ``username``, ``local``,
                             ``node``, ``server``, ``domain``, ``host``,
                             ``resource``, ``full``, ``jid``, or ``bare``.
        :param value: The new string value of the JID component.
        """
        if name == 'resource':
            self._jid = JID(self, resource=value)._jid
        elif name in ('user', 'username', 'local', 'node'):
            self._jid = JID(self, local=value)._jid
        elif name in ('server', 'domain', 'host'):
            self._jid = JID(self, domain=value)._jid
        elif name in ('full', 'jid'):
            self._jid = JID(value)._jid
        elif name == 'bare':
            parsed = JID(value)._jid
            self._jid = (parsed[0], parsed[1], self._jid[2])
        else:
            object.__setattr__(self, name, value)

    def __str__(self):
        """Use the full JID as the string value."""
        result = []
        if self._jid[0]:
            result.append(self._jid[0])
            result.append('@')
        if self._jid[1]:
            result.append(self._jid[1])
        if self._jid[2]:
            result.append('/')
            result.append(self._jid[2])
        return ''.join(result)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        """
        Two JIDs are considered equal if they have the same full JID value.
        """
        other = JID(other)
        return self._jid == other._jid

    def __ne__(self, other):
        """Two JIDs are considered unequal if they are not equal."""
        return not self._jid == other._jid

    def __hash__(self):
        """Hash a JID based on the string version of its full JID."""
        return hash(self.__str__())

    def __copy__(self):
        """Generate a duplicate JID."""
        return JID(self)
