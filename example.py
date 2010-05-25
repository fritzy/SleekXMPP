# coding=utf8

import sleekxmpp
import logging
from optparse import OptionParser
import time

import sys

if sys.version_info < (3,0):
	reload(sys)
	sys.setdefaultencoding('utf8')


class Example(sleekxmpp.ClientXMPP):
	
	def __init__(self, jid, password):
		sleekxmpp.ClientXMPP.__init__(self, jid, password)
		self.add_event_handler("session_start", self.start)
		self.add_event_handler("message", self.message)
	
	def start(self, event):
		self.getRoster()
		self.sendPresence()

	def message(self, msg):
		msg.reply("Thanks for sending\n%(body)s" % msg).send()

if __name__ == '__main__':
	#parse command line arguements
	optp = OptionParser()
	optp.add_option('-q','--quiet', help='set logging to ERROR', action='store_const', dest='loglevel', const=logging.ERROR, default=logging.INFO)
	optp.add_option('-d','--debug', help='set logging to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
	optp.add_option('-v','--verbose', help='set logging to COMM', action='store_const', dest='loglevel', const=5, default=logging.INFO)
	optp.add_option("-c","--config", dest="configfile", default="config.xml", help="set config file to use")
	opts,args = optp.parse_args()
	
	logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')
	xmpp = Example('user@gmail.com/sleekxmpp', 'password')
	xmpp.registerPlugin('xep_0030')	
	xmpp.registerPlugin('xep_0004')
	xmpp.registerPlugin('xep_0060')
	xmpp.registerPlugin('xep_0199')
	if xmpp.connect(('talk.google.com', 5222)):
		xmpp.process(threaded=False)
		print("done")
	else:
		print("Unable to connect.")
