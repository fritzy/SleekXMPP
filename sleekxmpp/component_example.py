import sleekxmpp.componentxmpp
import logging
from optparse import OptionParser
import time

class Example(sleekxmpp.componentxmpp.ComponentXMPP):
	
	def __init__(self, jid, password):
		sleekxmpp.componentxmpp.ComponentXMPP.__init__(self, jid, password, 'vm1', 5230)
		self.add_event_handler("session_start", self.start)
		self.add_event_handler("message", self.message)
	
	def start(self, event):
		#self.getRoster()
		#self.sendPresence(pto='admin@tigase.netflint.net/sarkozy')
		#self.sendPresence(pto='tigase.netflint.net')
		pass

	def message(self, event):
		self.sendMessage("%s/%s" % (event['jid'], event['resource']), "Thanks for sending me, \"%s\"." % event['message'], mtype=event['type'])

if __name__ == '__main__':
	#parse command line arguements
	optp = OptionParser()
	optp.add_option('-q','--quiet', help='set logging to ERROR', action='store_const', dest='loglevel', const=logging.ERROR, default=logging.INFO)
	optp.add_option('-d','--debug', help='set logging to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
	optp.add_option('-v','--verbose', help='set logging to COMM', action='store_const', dest='loglevel', const=5, default=logging.INFO)
	optp.add_option("-c","--config", dest="configfile", default="config.xml", help="set config file to use")
	opts,args = optp.parse_args()
	
	logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')
	xmpp = Example('component.vm1', 'secreteating')
	xmpp.registerPlugin('xep_0004')
	xmpp.registerPlugin('xep_0030')
	xmpp.registerPlugin('xep_0060')
	xmpp.registerPlugin('xep_0199')
	if xmpp.connect():
		xmpp.process(threaded=False)
		print("done")
	else:
		print("Unable to connect.")
