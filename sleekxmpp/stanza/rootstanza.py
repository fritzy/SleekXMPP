"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from .. xmlstream.stanzabase import StanzaBase
from xml.etree import cElementTree as ET
from . error import Error
from .. exceptions import XMPPError
import traceback
import sys

class RootStanza(StanzaBase):

	def exception(self, e): #called when a handler raises an exception
		self.reply()
		if isinstance(e, XMPPError): # we raised this deliberately
			self['error']['condition'] = e.condition
			self['error']['text'] = e.text
			if e.extension is not None: # extended error tag
				extxml = ET.Element("{%s}%s" % (e.extension_ns, e.extension), e.extension_args)
				self['error'].xml.append(extxml)
				self['error']['type'] = e.etype
		else: # we probably didn't raise this on purpose, so send back a traceback
			self['error']['condition'] = 'undefined-condition'
			if sys.version_info < (3,0):
				self['error']['text'] = "SleekXMPP got into trouble."
			else:
				self['error']['text'] = traceback.format_tb(e.__traceback__)
		self.send()

# all jabber:client root stanzas should have the error plugin
RootStanza.plugin_attrib_map['error'] = Error
RootStanza.plugin_tag_map["{%s}%s" % (Error.namespace, Error.name)] = Error
