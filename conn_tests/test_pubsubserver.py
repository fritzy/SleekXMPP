import logging
import sleekxmpp
from optparse import OptionParser
from xml.etree import cElementTree as ET
import os
import time
import sys
import thread
import unittest
import sleekxmpp.plugins.xep_0004
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
		self.failUnless(self.xmpp1['xep_0060'].create_node(self.pshost, 'testnode2', self.statev['defaultconfig']))
	
	def test005reconfigure(self):
		"""Retrieving node config and reconfiguring"""
		nconfig = self.xmpp1['xep_0060'].getNodeConfig(self.pshost, 'testnode2')
		self.failUnless(nconfig, "No configuration returned")
		#print("%s == %s" % (nconfig.getValues(), self.statev['defaultconfig'].getValues()))
		self.failUnless(nconfig.getValues() == self.statev['defaultconfig'].getValues(), "Configuration does not match")
		self.failUnless(self.xmpp1['xep_0060'].setNodeConfig(self.pshost, 'testnode2', nconfig))
	
	def test999cleanup(self):
		self.failUnless(self.xmpp1['xep_0060'].deleteNode(self.pshost, 'testnode2'))


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
	xmpp2.registerPlugin('xep_0004')
	xmpp2.registerPlugin('xep_0030')
	xmpp2.registerPlugin('xep_0060')
	xmpp2.registerPlugin('xep_0199')

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
	TestPubsubServer.pshost = 'pubsub.recon'
	xmpp1.waitforstart.get(True)
	xmpp2.waitforstart.get(True)
	testsuite = unittest.TestLoader().loadTestsFromTestCase(TestPubsubServer)

	alltests_suite = unittest.TestSuite([testsuite])
	result = unittest.TextTestRunner(verbosity=2).run(alltests_suite)
	xmpp1.disconnect()
	xmpp2.disconnect()
