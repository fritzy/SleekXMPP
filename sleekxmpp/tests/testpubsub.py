"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.
    
    See the file LICENSE for copying permission.
"""

import logging
import sleekxmpp
from optparse import OptionParser
from xml.etree import cElementTree as ET
import os
import time
import sys
import Queue
import thread


class testps(sleekxmpp.ClientXMPP):
	def __init__(self, jid, password, ssl=False, plugin_config = {}, plugin_whitelist=[], nodenum=0, pshost=None):
		sleekxmpp.ClientXMPP.__init__(self, jid, password, ssl, plugin_config, plugin_whitelist)
		self.registerPlugin('xep_0004')
		self.registerPlugin('xep_0030')
		self.registerPlugin('xep_0060')
		self.registerPlugin('xep_0092')
		self.add_handler("<message xmlns='jabber:client'><event xmlns='http://jabber.org/protocol/pubsub#event' /></message>", self.pubsubEventHandler, name='Pubsub Event', threaded=True)
		self.add_event_handler("session_start", self.start, threaded=True)
		self.add_handler("<iq type='error' />", self.handleError, name='Iq Error')
		self.events = Queue.Queue()
		self.default_config = None
		self.ps = self.plugin['xep_0060']
		self.node = "pstestnode_%s"
		self.pshost = pshost
		if pshost is None:
			self.pshost = self.server
		self.nodenum = int(nodenum)
		self.leafnode = self.nodenum + 1
		self.collectnode = self.nodenum + 2
		self.lasterror = ''
		self.sprintchars = 0
		self.defaultconfig = None
		self.tests = ['test_defaultConfig', 'test_createDefaultNode', 'test_getNodes', 'test_deleteNode', 'test_createWithConfig', 'test_reconfigureNode', 'test_subscribeToNode', 'test_addItem', 'test_updateItem', 'test_deleteItem', 'test_unsubscribeNode', 'test_createCollection', 'test_subscribeCollection', 'test_addNodeCollection', 'test_deleteNodeCollection', 'test_addCollectionNode', 'test_deleteCollectionNode', 'test_unsubscribeNodeCollection', 'test_deleteCollection']
		self.passed = 0
		self.width = 120
	
	def start(self, event):
		#TODO: make this configurable
		self.getRoster()
		self.sendPresence(ppriority=20)
		thread.start_new(self.test_all, tuple())
	
	def sprint(self, msg, end=False, color=False):
		length = len(msg)
		if color:
			if color == "red":
				color = "1;31"
			elif color == "green":
				color = "0;32"
			msg = "%s%s%s" % ("\033[%sm" % color, msg, "\033[0m")
		if not end:
			sys.stdout.write(msg)
			self.sprintchars += length
		else:
			self.sprint("%s%s" % ("." * (self.width - self.sprintchars - length), msg))
			print('')
			self.sprintchars = 0
		sys.stdout.flush()

	def pubsubEventHandler(self, xml):
		for item in xml.findall('{http://jabber.org/protocol/pubsub#event}event/{http://jabber.org/protocol/pubsub#event}items/{http://jabber.org/protocol/pubsub#event}item'):
			self.events.put(item.get('id', '__unknown__'))
		for item in xml.findall('{http://jabber.org/protocol/pubsub#event}event/{http://jabber.org/protocol/pubsub#event}items/{http://jabber.org/protocol/pubsub#event}retract'):
			self.events.put(item.get('id', '__unknown__'))
		for item in xml.findall('{http://jabber.org/protocol/pubsub#event}event/{http://jabber.org/protocol/pubsub#event}collection/{http://jabber.org/protocol/pubsub#event}disassociate'):
			self.events.put(item.get('node', '__unknown__'))
		for item in xml.findall('{http://jabber.org/protocol/pubsub#event}event/{http://jabber.org/protocol/pubsub#event}collection/{http://jabber.org/protocol/pubsub#event}associate'):
			self.events.put(item.get('node', '__unknown__'))
	
	def handleError(self, xml):
		error = xml.find('{jabber:client}error')
		self.lasterror =  error.getchildren()[0].tag.split('}')[-1]
		
	def test_all(self):
		print("Running Publish-Subscribe Tests")
		version = self.plugin['xep_0092'].getVersion(self.pshost)
		if version:
			print("%s %s on %s" % (version.get('name', 'Unknown Server'), version.get('version', 'v?'), version.get('os', 'Unknown OS')))
		print("=" * self.width)
		for test in self.tests:
			testfunc = getattr(self, test)
			self.sprint("%s" % testfunc.__doc__)
			if testfunc():
				self.sprint("Passed", True, "green")
				self.passed += 1
			else:
				if not self.lasterror:
					self.lasterror = 'No response'
				self.sprint("Failed (%s)" % self.lasterror, True, "red")
				self.lasterror = ''
		print("=" * self.width)
		self.sprint("Cleaning up...")
		#self.ps.deleteNode(self.pshost, self.node % self.nodenum)
		self.ps.deleteNode(self.pshost, self.node % self.leafnode)
		#self.ps.deleteNode(self.pshost, self.node % self.collectnode)
		self.sprint("Done", True, "green")
		self.disconnect()
		self.sprint("%s" % self.passed, False, "green")
		self.sprint("/%s Passed -- " % len(self.tests))
		if len(self.tests) - self.passed:
			self.sprint("%s" % (len(self.tests) - self.passed), False, "red")
		else:
			self.sprint("%s" % (len(self.tests) - self.passed), False, "green")
		self.sprint(" Failed Tests")
		print
		#print "%s/%s Passed -- %s Failed Tests" % (self.passed, len(self.tests), len(self.tests) - self.passed)
	
	def test_defaultConfig(self):
		"Retreiving default configuration"
		result = self.ps.getNodeConfig(self.pshost)
		if result is False or result is None:
			return False
		else:
			self.defaultconfig = result
			try:
				self.defaultconfig.field['pubsub#access_model'].setValue('open')
			except KeyError:
				pass
			try:
				self.defaultconfig.field['pubsub#notify_retract'].setValue(True)
			except KeyError:
				pass
			return True
	
	def test_createDefaultNode(self):
		"Creating default node"
		return self.ps.create_node(self.pshost, self.node % self.nodenum)
	
	def test_getNodes(self):
		"Getting list of nodes"
		self.ps.getNodes(self.pshost)
		self.ps.getItems(self.pshost, 'blog')
		return True
	
	def test_deleteNode(self):
		"Deleting node"
		return self.ps.deleteNode(self.pshost, self.node % self.nodenum)
	
	def test_createWithConfig(self):
		"Creating node with config"
		if self.defaultconfig is None:
			self.lasterror = "No Avail Config"
			return False
		return self.ps.create_node(self.pshost, self.node % self.leafnode, self.defaultconfig)
	
	def test_reconfigureNode(self):
		"Retrieving node config and reconfiguring"
		nconfig = self.ps.getNodeConfig(self.pshost, self.node % self.leafnode)
		if nconfig == False:
			return False
		return self.ps.setNodeConfig(self.pshost, self.node % self.leafnode, nconfig)
		
	def test_subscribeToNode(self):
		"Subscribing to node"
		return self.ps.subscribe(self.pshost, self.node % self.leafnode)
	
	def test_addItem(self):
		"Adding item, waiting for notification"
		item = ET.Element('test')
		result = self.ps.setItem(self.pshost, self.node % self.leafnode, (('test_node1', item),))
		if result == False:
			return False
		try:
			event = self.events.get(True, 10)
		except Queue.Empty:
			return False
		if event == 'test_node1':
			return True
		return False
	
	def test_updateItem(self):
		"Updating item, waiting for notification"
		item = ET.Element('test')
		item.attrib['crap'] = 'yup, right here'
		result = self.ps.setItem(self.pshost, self.node % self.leafnode, (('test_node1', item),))
		if result == False:
			return False
		try:
			event = self.events.get(True, 10)
		except Queue.Empty:
			return False
		if event == 'test_node1':
			return True
		return False

	def test_deleteItem(self):
		"Deleting item, waiting for notification"
		result = self.ps.deleteItem(self.pshost, self.node % self.leafnode, 'test_node1')
		if result == False:
			return False
		try:
			event = self.events.get(True, 10)
		except Queue.Empty:
			self.lasterror = "No Notification"
			return False
		if event == 'test_node1':
			return True
		return False
	
	def test_unsubscribeNode(self):
		"Unsubscribing from node"
		return self.ps.unsubscribe(self.pshost, self.node % self.leafnode)

	def test_createCollection(self):
		"Creating collection node"
		return self.ps.create_node(self.pshost, self.node % self.collectnode, self.defaultconfig, True)
	
	def test_subscribeCollection(self):
		"Subscribing to collection node"
		return self.ps.subscribe(self.pshost, self.node % self.collectnode)
	
	def test_addNodeCollection(self):
		"Assigning node to collection, waiting for notification"
		config = self.ps.getNodeConfig(self.pshost, self.node % self.leafnode)
		if not config or config is None:
			self.lasterror = "Config Error"
			return False
		try:
			config.field['pubsub#collection'].setValue(self.node % self.collectnode)
		except KeyError:
			self.sprint("...Missing Field...", False, "red")
			config.addField('pubsub#collection', value=self.node % self.collectnode)
		if not self.ps.setNodeConfig(self.pshost, self.node % self.leafnode, config):
			return False
		try:
			event = self.events.get(True, 10)
		except Queue.Empty:
			self.lasterror = "No Notification"
			return False
		if event == self.node % self.leafnode:
			return True
		return False
	
	def test_deleteNodeCollection(self):
		"Removing node assignment to collection, waiting for notification"
		config = self.ps.getNodeConfig(self.pshost, self.node % self.leafnode)
		if not config or config is None:
			self.lasterror = "Config Error"
			return False
		try:
			config.field['pubsub#collection'].delValue(self.node % self.collectnode)
		except KeyError:
			self.sprint("...Missing Field...", False, "red")
			config.addField('pubsub#collection', value='')
		if not self.ps.setNodeConfig(self.pshost, self.node % self.leafnode, config):
			return False
		try:
			event = self.events.get(True, 10)
		except Queue.Empty:
			self.lasterror = "No Notification"
			return False
		if event == self.node % self.leafnode:
			return True
		return False

	def test_addCollectionNode(self):
		"Assigning node from collection, waiting for notification"
		config = self.ps.getNodeConfig(self.pshost, self.node % self.collectnode)
		if not config or config is None:
			self.lasterror = "Config Error"
			return False
		try:
			config.field['pubsub#children'].setValue(self.node % self.leafnode)
		except KeyError:
			self.sprint("...Missing Field...", False, "red")
			config.addField('pubsub#children', value=self.node % self.leafnode)
		if not self.ps.setNodeConfig(self.pshost, self.node % self.collectnode, config):
			return False
		try:
			event = self.events.get(True, 10)
		except Queue.Empty:
			self.lasterror = "No Notification"
			return False
		if event == self.node % self.leafnode:
			return True
		return False

	def test_deleteCollectionNode(self):
		"Removing node from collection, waiting for notification"
		config = self.ps.getNodeConfig(self.pshost, self.node % self.collectnode)
		if not config or config is None:
			self.lasterror = "Config Error"
			return False
		try:
			config.field['pubsub#children'].delValue(self.node % self.leafnode)
		except KeyError:
			self.sprint("...Missing Field...", False, "red")
			config.addField('pubsub#children', value='')
		if not self.ps.setNodeConfig(self.pshost, self.node % self.collectnode, config):
			return False
		try:
			event = self.events.get(True, 10)
		except Queue.Empty:
			self.lasterror = "No Notification"
			return False
		if event == self.node % self.leafnode:
			return True
		return False
	
	def test_unsubscribeNodeCollection(self):
		"Unsubscribing from collection"
		return self.ps.unsubscribe(self.pshost, self.node % self.collectnode)
	
	def test_deleteCollection(self):
		"Deleting collection"
		return self.ps.deleteNode(self.pshost, self.node % self.collectnode)

if __name__ == '__main__':
	#parse command line arguements
	optp = OptionParser()
	optp.add_option('-q','--quiet', help='set logging to ERROR', action='store_const', dest='loglevel', const=logging.ERROR, default=logging.INFO)
	optp.add_option('-d','--debug', help='set logging to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
	optp.add_option('-v','--verbose', help='set logging to COMM', action='store_const', dest='loglevel', const=5, default=logging.INFO)
	optp.add_option("-c","--config", dest="configfile", default="config.xml", help="set config file to use")
	optp.add_option("-n","--nodenum", dest="nodenum", default="1", help="set node number to use")
	optp.add_option("-p","--pubsub", dest="pubsub", default="1", help="set pubsub host to use")
	opts,args = optp.parse_args()
	
	logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')

	#load xml config
	logging.info("Loading config file: %s" % opts.configfile)
	config = ET.parse(os.path.expanduser(opts.configfile)).find('auth')
	
	#init
	logging.info("Logging in as %s" % config.attrib['jid'])
	
	
	plugin_config = {}
	plugin_config['xep_0092'] = {'name': 'SleekXMPP Example', 'version': '0.1-dev'}
	plugin_config['xep_0199'] = {'keepalive': True, 'timeout': 30, 'frequency': 300}
	
	con = testps(config.attrib['jid'], config.attrib['pass'], plugin_config=plugin_config, plugin_whitelist=[], nodenum=opts.nodenum, pshost=opts.pubsub)
	if not config.get('server', None):
		# we don't know the server, but the lib can probably figure it out
		con.connect() 
	else:
		con.connect((config.attrib['server'], 5222))
	con.process(threaded=False)
	print("")
