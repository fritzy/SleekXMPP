"""
	SleekXMPP: The Sleek XMPP Library
	Copyright (C) 2007  Nathanael C. Fritz
	This file is part of SleekXMPP.

	SleekXMPP is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 2 of the License, or
	(at your option) any later version.

	SleekXMPP is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with SleekXMPP; if not, write to the Free Software
	Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
class base_plugin(object):
	
	def __init__(self, xmpp, config):
		self.xep = 'base'
		self.description = 'Base Plugin'
		self.xmpp = xmpp
		self.config = config
		self.post_inited = False
		self.enable = config.get('enable', True)
		if self.enable:
			self.plugin_init()
	
	def plugin_init(self):
		pass
	
	def post_init(self):
		self.post_inited = True
