"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Iq
from sleekxmpp.xmlstream import JID
from sleekxmpp.xmlstream.stanzabase import registerStanzaPlugin
from sleekxmpp.xmlstream.stanzabase import ET, ElementBase


class Roster(ElementBase):

    """
    Example roster stanzas:
        <iq type="set">
          <query xmlns="jabber:iq:roster">
            <item jid="user@example.com" subscription="both" name="User">
              <group>Friends</group>
            </item>
          </query>
        </iq>

    Stanza Inteface:
        items -- A dictionary of roster entries contained
                 in the stanza.

    Methods:
        getItems -- Return a dictionary of roster entries.
        setItems -- Add <item> elements.
        delItems -- Remove all <item> elements.
    """

    namespace = 'jabber:iq:roster'
    name = 'query'
    plugin_attrib = 'roster'
    interfaces = set(('items',))

    def setItems(self, items):
        """
        Set the roster entries in the <roster> stanza.

        Uses a dictionary using JIDs as keys, where each entry is itself
        a dictionary that contains:
            name         -- An alias or nickname for the JID.
            subscription -- The subscription type. Can be one of 'to',
                            'from', 'both', 'none', or 'remove'.
            groups       -- A list of group names to which the JID
                            has been assigned.

        Arguments:
            items -- A dictionary of roster entries.
        """
        self.delItems()
        for jid in items:
            ijid = str(jid)
            item = ET.Element('{jabber:iq:roster}item', {'jid': ijid})
            if 'subscription' in items[jid]:
                item.attrib['subscription'] = items[jid]['subscription']
            if 'name' in items[jid]:
                name = items[jid]['name']
                if name is not None:
                    item.attrib['name'] = name
            if 'groups' in items[jid]:
                for group in items[jid]['groups']:
                    groupxml = ET.Element('{jabber:iq:roster}group')
                    groupxml.text = group
                    item.append(groupxml)
            self.xml.append(item)
        return self

    def getItems(self):
        """
        Return a dictionary of roster entries.

        Each item is keyed using its JID, and contains:
            name         -- An assigned alias or nickname for the JID.
            subscription -- The subscription type. Can be one of 'to',
                            'from', 'both', 'none', or 'remove'.
            groups       -- A list of group names to which the JID has
                            been assigned.
        """
        items = {}
        itemsxml = self.xml.findall('{jabber:iq:roster}item')
        if itemsxml is not None:
            for itemxml in itemsxml:
                item = {}
                item['name'] = itemxml.get('name', '')
                item['subscription'] = itemxml.get('subscription', '')
                item['groups'] = []
                groupsxml = itemxml.findall('{jabber:iq:roster}group')
                if groupsxml is not None:
                    for groupxml in groupsxml:
                        item['groups'].append(groupxml.text)
                items[itemxml.get('jid')] = item
        return items

    def delItems(self):
        """
        Remove all <item> elements from the roster stanza.
        """
        for child in self.xml.getchildren():
            self.xml.remove(child)


registerStanzaPlugin(Iq, Roster)
