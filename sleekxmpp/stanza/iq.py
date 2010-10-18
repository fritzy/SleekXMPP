"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Error
from sleekxmpp.stanza.rootstanza import RootStanza
from sleekxmpp.xmlstream import RESPONSE_TIMEOUT, StanzaBase, ET
from sleekxmpp.xmlstream.handler import Waiter
from sleekxmpp.xmlstream.matcher import MatcherId


class Iq(RootStanza):

    """
    XMPP <iq> stanzas, or info/query stanzas, are XMPP's method of
    requesting and modifying information, similar to HTTP's GET and
    POST methods.

    Each <iq> stanza must have an 'id' value which associates the
    stanza with the response stanza. XMPP entities must always
    be given a response <iq> stanza with a type of 'result' after
    sending a stanza of type 'get' or 'set'.

    Most uses cases for <iq> stanzas will involve adding a <query>
    element whose namespace indicates the type of information
    desired. However, some custom XMPP applications use <iq> stanzas
    as a carrier stanza for an application-specific protocol instead.

    Example <iq> Stanzas:
        <iq to="user@example.com" type="get" id="314">
          <query xmlns="http://jabber.org/protocol/disco#items" />
        </iq>

        <iq to="user@localhost" type="result" id="17">
          <query xmlns='jabber:iq:roster'>
            <item jid='otheruser@example.net'
                  name='John Doe'
                  subscription='both'>
              <group>Friends</group>
            </item>
          </query>
        </iq>

    Stanza Interface:
        query -- The namespace of the <query> element if one exists.

    Attributes:
        types -- May be one of: get, set, result, or error.

    Methods:
        __init__    -- Overrides StanzaBase.__init__.
        unhandled   -- Send error if there are no handlers.
        set_payload -- Overrides StanzaBase.set_payload.
        set_query   -- Add or modify a <query> element.
        get_query   -- Return the namespace of the <query> element.
        del_query   -- Remove the <query> element.
        reply       -- Overrides StanzaBase.reply
        send        -- Overrides StanzaBase.send
    """

    namespace = 'jabber:client'
    name = 'iq'
    interfaces = set(('type', 'to', 'from', 'id', 'query'))
    types = set(('get', 'result', 'set', 'error'))
    plugin_attrib = name

    def __init__(self, *args, **kwargs):
        """
        Initialize a new <iq> stanza with an 'id' value.

        Overrides StanzaBase.__init__.
        """
        StanzaBase.__init__(self, *args, **kwargs)
        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.setPayload = self.set_payload
        self.getQuery = self.get_query
        self.setQuery = self.set_query
        self.delQuery = self.del_query

        if self['id'] == '':
            if self.stream is not None:
                self['id'] = self.stream.getNewId()
            else:
                self['id'] = '0'

    def unhandled(self):
        """
        Send a feature-not-implemented error if the stanza is not handled.

        Overrides StanzaBase.unhandled.
        """
        if self['type'] in ('get', 'set'):
            self.reply()
            self['error']['condition'] = 'feature-not-implemented'
            self['error']['text'] = 'No handlers registered for this request.'
            self.send()

    def set_payload(self, value):
        """
        Set the XML contents of the <iq> stanza.

        Arguments:
            value -- An XML object to use as the <iq> stanza's contents
        """
        self.clear()
        StanzaBase.set_payload(self, value)
        return self

    def set_query(self, value):
        """
        Add or modify a <query> element.

        Query elements are differentiated by their namespace.

        Arguments:
            value -- The namespace of the <query> element.
        """
        query = self.xml.find("{%s}query" % value)
        if query is None and value:
            self.clear()
            query = ET.Element("{%s}query" % value)
            self.xml.append(query)
        return self

    def get_query(self):
        """Return the namespace of the <query> element."""
        for child in self.xml.getchildren():
            if child.tag.endswith('query'):
                ns = child.tag.split('}')[0]
                if '{' in ns:
                    ns = ns[1:]
                return ns
        return ''

    def del_query(self):
        """Remove the <query> element."""
        for child in self.xml.getchildren():
            if child.tag.endswith('query'):
                self.xml.remove(child)
        return self

    def reply(self):
        """
        Send a reply <iq> stanza.

        Overrides StanzaBase.reply

        Sets the 'type' to 'result' in addition to the default
        StanzaBase.reply behavior.
        """
        self['type'] = 'result'
        StanzaBase.reply(self)
        return self

    def send(self, block=True, timeout=RESPONSE_TIMEOUT):
        """
        Send an <iq> stanza over the XML stream.

        The send call can optionally block until a response is received or
        a timeout occurs. Be aware that using blocking in non-threaded event
        handlers can drastically impact performance.

        Overrides StanzaBase.send

        Arguments:
            block   -- Specify if the send call will block until a response
                       is received, or a timeout occurs. Defaults to True.
            timeout -- The length of time (in seconds) to wait for a response
                       before exiting the send call if blocking is used.
                       Defaults to sleekxmpp.xmlstream.RESPONSE_TIMEOUT
        """
        if block and self['type'] in ('get', 'set'):
            waitfor = Waiter('IqWait_%s' % self['id'], MatcherId(self['id']))
            self.stream.registerHandler(waitfor)
            StanzaBase.send(self)
            return waitfor.wait(timeout)
        else:
            return StanzaBase.send(self)
