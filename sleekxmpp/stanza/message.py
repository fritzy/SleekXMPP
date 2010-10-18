"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Error
from sleekxmpp.stanza.rootstanza import RootStanza
from sleekxmpp.xmlstream import StanzaBase, ET


class Message(RootStanza):

    """
    XMPP's <message> stanzas are a "push" mechanism to send information
    to other XMPP entities without requiring a response.

    Chat clients will typically use <message> stanzas that have a type
    of either "chat" or "groupchat".

    When handling a message event, be sure to check if the message is
    an error response.

    Example <message> stanzas:
        <message to="user1@example.com" from="user2@example.com">
          <body>Hi!</body>
        </message>

        <message type="groupchat" to="room@conference.example.com">
          <body>Hi everyone!</body>
        </message>

    Stanza Interface:
        body    -- The main contents of the message.
        subject -- An optional description of the message's contents.
        mucroom -- (Read-only) The name of the MUC room that sent the message.
        mucnick -- (Read-only) The MUC nickname of message's sender.

    Attributes:
        types -- May be one of: normal, chat, headline, groupchat, or error.

    Methods:
        setup       -- Overrides StanzaBase.setup.
        chat        -- Set the message type to 'chat'.
        normal      -- Set the message type to 'normal'.
        reply       -- Overrides StanzaBase.reply
        get_type    -- Overrides StanzaBase interface
        get_mucroom -- Return the name of the MUC room of the message.
        set_mucroom -- Dummy method to prevent assignment.
        del_mucroom -- Dummy method to prevent deletion.
        get_mucnick -- Return the MUC nickname of the message's sender.
        set_mucnick -- Dummy method to prevent assignment.
        del_mucnick -- Dummy method to prevent deletion.
    """

    namespace = 'jabber:client'
    name = 'message'
    interfaces = set(('type', 'to', 'from', 'id', 'body', 'subject',
                      'mucroom', 'mucnick'))
    sub_interfaces = set(('body', 'subject'))
    plugin_attrib = name
    types = set((None, 'normal', 'chat', 'headline', 'error', 'groupchat'))

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides StanzaBase.setup.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.getType = self.get_type
        self.getMucroom = self.get_mucroom
        self.setMucroom = self.set_mucroom
        self.delMucroom = self.del_mucroom
        self.getMucnick = self.get_mucnick
        self.setMucnick = self.set_mucnick
        self.delMucnick = self.del_mucnick

        return StanzaBase.setup(self, xml)

    def get_type(self):
        """
        Return the message type.

        Overrides default stanza interface behavior.

        Returns 'normal' if no type attribute is present.
        """
        return self._get_attr('type', 'normal')

    def chat(self):
        """Set the message type to 'chat'."""
        self['type'] = 'chat'
        return self

    def normal(self):
        """Set the message type to 'chat'."""
        self['type'] = 'normal'
        return self

    def reply(self, body=None):
        """
        Create a message reply.

        Overrides StanzaBase.reply.

        Sets proper 'to' attribute if the message is from a MUC, and
        adds a message body if one is given.

        Arguments:
            body -- Optional text content for the message.
        """
        StanzaBase.reply(self)
        if self['type'] == 'groupchat':
            self['to'] = self['to'].bare

        del self['id']

        if body is not None:
            self['body'] = body
        return self

    def get_mucroom(self):
        """
        Return the name of the MUC room where the message originated.

        Read-only stanza interface.
        """
        if self['type'] == 'groupchat':
            return self['from'].bare
        else:
            return ''

    def get_mucnick(self):
        """
        Return the nickname of the MUC user that sent the message.

        Read-only stanza interface.
        """
        if self['type'] == 'groupchat':
            return self['from'].resource
        else:
            return ''

    def set_mucroom(self, value):
        """Dummy method to prevent modification."""
        pass

    def del_mucroom(self):
        """Dummy method to prevent deletion."""
        pass

    def set_mucnick(self, value):
        """Dummy method to prevent modification."""
        pass

    def del_mucnick(self):
        """Dummy method to prevent deletion."""
        pass
