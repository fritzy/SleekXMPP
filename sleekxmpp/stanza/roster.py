"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.stanza import Iq
from sleekxmpp.xmlstream import JID
from sleekxmpp.xmlstream import ET, ElementBase, register_stanza_plugin


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
        get_items -- Return a dictionary of roster entries.
        set_items -- Add <item> elements.
        del_items -- Remove all <item> elements.
    """

    namespace = 'jabber:iq:roster'
    name = 'query'
    plugin_attrib = 'roster'
    interfaces = set(('items',))

    def setup(self, xml=None):
        """
        Populate the stanza object using an optional XML object.

        Overrides StanzaBase.setup.

        Arguments:
            xml -- Use an existing XML object for the stanza's values.
        """
        # To comply with PEP8, method names now use underscores.
        # Deprecated method names are re-mapped for backwards compatibility.
        self.setItems = self.set_items
        self.getItems = self.get_items
        self.delItems = self.del_items

        return ElementBase.setup(self, xml)

    def set_items(self, items):
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
        self.del_items()
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

    def get_items(self):
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

    def del_items(self):
        """
        Remove all <item> elements from the roster stanza.
        """
        for child in self.xml.getchildren():
            self.xml.remove(child)


register_stanza_plugin(Iq, Roster)
