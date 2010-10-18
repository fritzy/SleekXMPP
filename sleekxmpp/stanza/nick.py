"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Message, Presence
from sleekxmpp.xmlstream import ElementBase, ET, register_stanza_plugin


class Nick(ElementBase):

    """
    XEP-0172: User Nickname allows the addition of a <nick> element
    in several stanza types, including <message> and <presence> stanzas.

    The nickname contained in a <nick> should be the global, friendly or
    informal name chosen by the owner of a bare JID. The <nick> element
    may be included when establishing communications with new entities,
    such as normal XMPP users or MUC services.

    The nickname contained in a <nick> element will not necessarily be
    the same as the nickname used in a MUC.

    Example stanzas:
        <message to="user@example.com">
          <nick xmlns="http://jabber.org/nick/nick">The User</nick>
          <body>...</body>
        </message>

        <presence to="otheruser@example.com" type="subscribe">
          <nick xmlns="http://jabber.org/nick/nick">The User</nick>
        </presence>

    Stanza Interface:
        nick -- A global, friendly or informal name chosen by a user.

    Methods:
        setup    -- Overrides ElementBase.setup.
        get_nick -- Return the nickname in the <nick> element.
        set_nick -- Add a <nick> element with the given nickname.
        del_nick -- Remove the <nick> element.
    """

    namespace = 'http://jabber.org/nick/nick'
    name = 'nick'
    plugin_attrib = name
    interfaces = set(('nick',))

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides StanzaBase.setup.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.setNick = self.set_nick
        self.getNick = self.get_nick
        self.delNick = self.del_nick

        return ElementBase.setup(self, xml)

    def set_nick(self, nick):
        """
        Add a <nick> element with the given nickname.

        Arguments:
            nick -- A human readable, informal name.
        """
        self.xml.text = nick

    def get_nick(self):
        """Return the nickname in the <nick> element."""
        return self.xml.text

    def del_nick(self):
        """Remove the <nick> element."""
        if self.parent is not None:
            self.parent().xml.remove(self.xml)


register_stanza_plugin(Message, Nick)
register_stanza_plugin(Presence, Nick)
