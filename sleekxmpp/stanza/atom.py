from .. xmlstream.stanzabase import registerStanzaPlugin, ElementBase, ET, JID
from xml.etree import cElementTree as ET

class AtomEntry(ElementBase):
	namespace = 'http://www.w3.org/2005/Atom'
	name = 'entry'
	plugin_attrib = 'entry'
	interfaces = set(('title', 'summary'))
	sub_interfaces = set(('title', 'summary'))
	plugin_attrib_map = {}
	plugin_tag_map = {}
