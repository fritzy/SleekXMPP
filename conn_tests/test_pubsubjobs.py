import logging
import sleekxmpp
from optparse import OptionParser
from xml.etree import cElementTree as ET
import os
import time
import sys
import unittest
import sleekxmpp.plugins.xep_0004
from sleekxmpp.xmlstream.matcher.stanzapath import StanzaPath
from sleekxmpp.xmlstream.handler.waiter import Waiter
try:
	import configparser
except ImportError:
	import ConfigParser as configparser
try:
	import queue
except ImportError:
	import Queue as queue

class TestClient(sleekxmpp.ClientXMPP):
	def __init__(self, jid, password):
		sleekxmpp.ClientXMPP.__init__(self, jid, password)
		self.add_event_handler("session_start", self.start)
		#self.add_event_handler("message", self.message)
		self.waitforstart = queue.Queue()
	
	def start(self, event):
		self.getRoster()
		self.sendPresence()
		self.waitforstart.put(True)


class TestPubsubServer(unittest.TestCase):
	statev = {}

	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)

	def setUp(self):
		pass

	def test001getdefaultconfig(self):
		"""Get the default node config"""
		self.xmpp1['xep_0060'].deleteNode(self.pshost, 'testnode2')
		self.xmpp1['xep_0060'].deleteNode(self.pshost, 'testnode3')
		self.xmpp1['xep_0060'].deleteNode(self.pshost, 'testnode4')
		self.xmpp1['xep_0060'].deleteNode(self.pshost, 'testnode5')
		result = self.xmpp1['xep_0060'].getNodeConfig(self.pshost)
		self.statev['defaultconfig'] = result
		self.failUnless(isinstance(result, sleekxmpp.plugins.xep_0004.Form))
	
	def test002createdefaultnode(self):
		"""Create a node without config"""
		self.failUnless(self.xmpp1['xep_0060'].create_node(self.pshost, 'testnode1'))

	def test003deletenode(self):
		"""Delete recently created node"""
		self.failUnless(self.xmpp1['xep_0060'].deleteNode(self.pshost, 'testnode1'))
	
	def test004createnode(self):
		"""Create a node with a config"""
		self.statev['defaultconfig'].field['pubsub#access_model'].setValue('open')
		self.statev['defaultconfig'].field['pubsub#notify_retract'].setValue(True)
		self.statev['defaultconfig'].field['pubsub#persist_items'].setValue(True)
		self.statev['defaultconfig'].field['pubsub#presence_based_delivery'].setValue(True)
		p = self.xmpp2.Presence()
		p['to'] = self.pshost
		p.send()
		self.failUnless(self.xmpp1['xep_0060'].create_node(self.pshost, 'testnode2', self.statev['defaultconfig'], ntype='job'))
	
	def test005reconfigure(self):
		"""Retrieving node config and reconfiguring"""
		nconfig = self.xmpp1['xep_0060'].getNodeConfig(self.pshost, 'testnode2')
		self.failUnless(nconfig, "No configuration returned")
		#print("\n%s ==\n %s" % (nconfig.getValues(), self.statev['defaultconfig'].getValues()))
		self.failUnless(nconfig.getValues() == self.statev['defaultconfig'].getValues(), "Configuration does not match")
		self.failUnless(self.xmpp1['xep_0060'].setNodeConfig(self.pshost, 'testnode2', nconfig))

	def test006subscribetonode(self):
		"""Subscribe to node from account 2"""
		self.failUnless(self.xmpp2['xep_0060'].subscribe(self.pshost, "testnode2"))
	
	def test007publishitem(self):
		"""Publishing item"""
		item = ET.Element('{http://netflint.net/protocol/test}test')
		w = Waiter('wait publish', StanzaPath('message/pubsub_event/items'))
		self.xmpp2.registerHandler(w)
		#result = self.xmpp1['xep_0060'].setItem(self.pshost, "testnode2", (('test1', item),))
		result = self.xmpp1['jobs'].createJob(self.pshost, "testnode2", 'test1', item)
		msg = w.wait(5) # got to get a result in 5 seconds
		self.failUnless(msg != False, "Account #2 did not get message event")
		#result = self.xmpp1['xep_0060'].setItem(self.pshost, "testnode2", (('test2', item),))
		result = self.xmpp1['jobs'].createJob(self.pshost, "testnode2", 'test2', item)
		w = Waiter('wait publish2', StanzaPath('message/pubsub_event/items'))
		self.xmpp2.registerHandler(w)
		self.xmpp2['jobs'].claimJob(self.pshost, 'testnode2', 'test1')
		msg = w.wait(5) # got to get a result in 5 seconds
		self.xmpp2['jobs'].claimJob(self.pshost, 'testnode2', 'test2')
		self.xmpp2['jobs'].finishJob(self.pshost, 'testnode2', 'test1')
		self.xmpp2['jobs'].finishJob(self.pshost, 'testnode2', 'test2')
		print result
		#need to add check for update

	def test900cleanup(self):
		"Cleaning up"
		#self.failUnless(self.xmpp1['xep_0060'].deleteNode(self.pshost, 'testnode2'), "Could not delete test node.")
		time.sleep(10)
	

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
	config = configparser.RawConfigParser()
	config.read(opts.configfile)
	
	#init
	logging.info("Account 1 is %s" % config.get('account1', 'jid'))
	xmpp1 = TestClient(config.get('account1','jid'), config.get('account1','pass'))
	logging.info("Account 2 is %s" % config.get('account2', 'jid'))
	xmpp2 = TestClient(config.get('account2','jid'), config.get('account2','pass'))
	
	xmpp1.registerPlugin('xep_0004')
	xmpp1.registerPlugin('xep_0030')
	xmpp1.registerPlugin('xep_0060')
	xmpp1.registerPlugin('xep_0199')
	xmpp1.registerPlugin('jobs')
	xmpp2.registerPlugin('xep_0004')
	xmpp2.registerPlugin('xep_0030')
	xmpp2.registerPlugin('xep_0060')
	xmpp2.registerPlugin('xep_0199')
	xmpp2.registerPlugin('jobs')

	if not config.get('account1', 'server'):
		# we don't know the server, but the lib can probably figure it out
		xmpp1.connect() 
	else:
		xmpp1.connect((config.get('account1', 'server'), 5222))
	xmpp1.process(threaded=True)
	
	#init
	if not config.get('account2', 'server'):
		# we don't know the server, but the lib can probably figure it out
		xmpp2.connect() 
	else:
		xmpp2.connect((config.get('account2', 'server'), 5222))
	xmpp2.process(threaded=True)

	TestPubsubServer.xmpp1 = xmpp1
	TestPubsubServer.xmpp2 = xmpp2
	TestPubsubServer.pshost = config.get('settings', 'pubsub')
	xmpp1.waitforstart.get(True)
	xmpp2.waitforstart.get(True)
	testsuite = unittest.TestLoader().loadTestsFromTestCase(TestPubsubServer)

	alltests_suite = unittest.TestSuite([testsuite])
	result = unittest.TextTestRunner(verbosity=2).run(alltests_suite)
	xmpp1.disconnect()
	xmpp2.disconnect()
