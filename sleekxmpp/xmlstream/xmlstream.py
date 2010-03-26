"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""

from __future__ import with_statement, unicode_literals
try:
	import queue
except ImportError:
	import Queue as queue
from . import statemachine
from . stanzabase import StanzaBase
from xml.etree import cElementTree
from xml.parsers import expat
import logging
import socket
import threading
import time
import traceback
import types
import xml.sax.saxutils

HANDLER_THREADS = 1

ssl_support = True
#try:
import ssl
#except ImportError:
#	ssl_support = False
import sys
if sys.version_info < (3, 0):
	#monkey patch broken filesocket object
	from . import filesocket
	#socket._fileobject = filesocket.filesocket
	

class RestartStream(Exception):
	pass

class CloseStream(Exception):
	pass

stanza_extensions = {}

class XMLStream(object):
	"A connection manager with XML events."

	def __init__(self, socket=None, host='', port=0, escape_quotes=False):
		global ssl_support
		self.ssl_support = ssl_support
		self.escape_quotes = escape_quotes
		self.state = statemachine.StateMachine()
		self.state.addStates({'connected':False, 'is client':False, 'ssl':False, 'tls':False, 'reconnect':True, 'processing':False}) #set initial states

		self.setSocket(socket)
		self.address = (host, int(port))

		self.__thread = {}

		self.__root_stanza = []
		self.__stanza = {}
		self.__stanza_extension = {}
		self.__handlers = []

		self.__tls_socket = None
		self.filesocket = None
		self.use_ssl = False
		self.use_tls = False

		self.stream_header = "<stream>"
		self.stream_footer = "</stream>"

		self.eventqueue = queue.Queue()
		self.sendqueue = queue.Queue()

		self.namespace_map = {}

		self.run = True
	
	def setSocket(self, socket):
		"Set the socket"
		self.socket = socket
		if socket is not None:
			self.filesocket = socket.makefile('rb', 0) # ElementTree.iterparse requires a file.  0 buffer files have to be binary
			self.state.set('connected', True)

	
	def setFileSocket(self, filesocket):
		self.filesocket = filesocket
	
	def connect(self, host='', port=0, use_ssl=False, use_tls=True):
		"Link to connectTCP"
		return self.connectTCP(host, port, use_ssl, use_tls)

	def connectTCP(self, host='', port=0, use_ssl=None, use_tls=None, reattempt=True):
		"Connect and create socket"
		while reattempt and not self.state['connected']:
			if host and port:
				self.address = (host, int(port))
			if use_ssl is not None:
				self.use_ssl = use_ssl
			if use_tls is not None:
				self.use_tls = use_tls
			self.state.set('is client', True)
			if sys.version_info < (3, 0):
				self.socket = filesocket.Socket26(socket.AF_INET, socket.SOCK_STREAM)
			else:
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.settimeout(None)
			if self.use_ssl and self.ssl_support:
				logging.debug("Socket Wrapped for SSL")
				self.socket = ssl.wrap_socket(self.socket)
			try:
				self.socket.connect(self.address)
				#self.filesocket = self.socket.makefile('rb', 0)
				self.filesocket = self.socket.makefile('rb', 0)
				self.state.set('connected', True)
				return True
			except socket.error as serr:
				logging.error("Could not connect. Socket Error #%s: %s" % (serr.errno, serr.strerror))
				time.sleep(1)
	
	def connectUnix(self, filepath):
		"Connect to Unix file and create socket"

	def startTLS(self):
		"Handshakes for TLS"
		if self.ssl_support:
			logging.info("Negotiating TLS")
			self.realsocket = self.socket
			self.socket = ssl.wrap_socket(self.socket, ssl_version=ssl.PROTOCOL_TLSv1, do_handshake_on_connect=False)
			self.socket.do_handshake()
			if sys.version_info < (3,0):
				from . filesocket import filesocket
				self.filesocket = filesocket(self.socket)
			else:
				self.filesocket = self.socket.makefile('rb', 0)
			return True
		else:
			logging.warning("Tried to enable TLS, but ssl module not found.")
			return False
		raise RestartStream()
	
	def process(self, threaded=True):
		for t in range(0, HANDLER_THREADS):
			self.__thread['eventhandle%s' % t] = threading.Thread(name='eventhandle%s' % t, target=self._eventRunner)
			self.__thread['eventhandle%s' % t].start()
		self.__thread['sendthread'] = threading.Thread(name='sendthread', target=self._sendThread)
		self.__thread['sendthread'].start()
		if threaded:
			self.__thread['process'] = threading.Thread(name='process', target=self._process)
			self.__thread['process'].start()
		else:
			self._process()
	
	def schedule(self, seconds, handler, args=None):
		threading.Timer(seconds, handler, args).start()
	
	def _process(self):
		"Start processing the socket."
		firstrun = True
		while self.run and (firstrun or self.state['reconnect']):
			self.state.set('processing', True)
			firstrun = False
			try:
				if self.state['is client']:
					self.sendRaw(self.stream_header)
				while self.__readXML():
					if self.state['is client']:
						self.sendRaw(self.stream_header)
			except KeyboardInterrupt:
				logging.debug("Keyboard Escape Detected")
				self.state.set('processing', False)
				self.state.set('reconnect', False)
				self.disconnect()
				self.run = False
				self.eventqueue.put(('quit', None, None))
				return
			except CloseStream:
				return
			except SystemExit:
				self.eventqueue.put(('quit', None, None))
				return
			except socket.error:
				if not self.state.reconnect:
					return
				else:
					self.state.set('processing', False)
					traceback.print_exc()
					self.disconnect(reconnect=True)
			except:
				if not self.state.reconnect:
					return
				else:
					self.state.set('processing', False)
					traceback.print_exc()
					self.disconnect(reconnect=True)
			if self.state['reconnect']:
				self.reconnect()
			self.state.set('processing', False)
			self.eventqueue.put(('quit', None, None))
		#self.__thread['readXML'] = threading.Thread(name='readXML', target=self.__readXML)
		#self.__thread['readXML'].start()
		#self.__thread['spawnEvents'] = threading.Thread(name='spawnEvents', target=self.__spawnEvents)
		#self.__thread['spawnEvents'].start()
	
	def __readXML(self):
		"Parses the incoming stream, adding to xmlin queue as it goes"
		#build cElementTree object from expat was we go
		#self.filesocket = self.socket.makefile('rb', 0)
		#print self.filesocket.read(1024) #self.filesocket._sock.recv(1024)
		edepth = 0
		root = None
		for (event, xmlobj) in cElementTree.iterparse(self.filesocket, (b'end', b'start')):
			if edepth == 0: # and xmlobj.tag.split('}', 1)[-1] == self.basetag:
				if event == b'start':
					root = xmlobj
					self.start_stream_handler(root)
			if event == b'end':
				edepth += -1
				if edepth == 0 and event == b'end':
					return False
				elif edepth == 1:
					#self.xmlin.put(xmlobj)
					try:
						self.__spawnEvent(xmlobj)
					except RestartStream:
						return True
					except CloseStream:
						return False
					if root:
						root.clear()
			if event == b'start':
				edepth += 1
	
	def _sendThread(self):
		while self.run:
			data = self.sendqueue.get(True)
			logging.debug("SEND: %s" % data)
			try:
				self.socket.send(data.encode('utf-8'))
				#self.socket.send(bytes(data, "utf-8"))
				#except socket.error,(errno, strerror):
			except:
				self.state.set('connected', False)
				if self.state.reconnect:
					logging.error("Disconnected. Socket Error.")
					traceback.print_exc()
					self.disconnect(reconnect=True)
	
	def sendRaw(self, data):
		self.sendqueue.put(data)
		return True
	
	def disconnect(self, reconnect=False):
		self.state.set('reconnect', reconnect)
		if self.state['connected']:
			self.sendRaw(self.stream_footer)
			#send end of stream
			#wait for end of stream back
		try:
			self.socket.close()
			self.filesocket.close()
			self.socket.shutdown(socket.SHUT_RDWR)
		except socket.error as serr:
			#logging.warning("Error while disconnecting. Socket Error #%s: %s" % (errno, strerror))
			#thread.exit_thread()
			pass
		if self.state['processing']:
			#raise CloseStream
			pass
	
	def reconnect(self):
		self.state.set('tls',False)
		self.state.set('ssl',False)
		time.sleep(1)
		self.connect()
	
	def incoming_filter(self, xmlobj):
		return xmlobj
		
	def __spawnEvent(self, xmlobj):
		"watching xmlOut and processes handlers"
		#convert XML into Stanza
		logging.debug("RECV: %s" % cElementTree.tostring(xmlobj))
		xmlobj = self.incoming_filter(xmlobj)
		stanza = None
		for stanza_class in self.__root_stanza:
			if xmlobj.tag == "{%s}%s" % (self.default_ns, stanza_class.name):
			#if self.__root_stanza[stanza_class].match(xmlobj):
				stanza = stanza_class(self, xmlobj)
				break
		if stanza is None:
			stanza = StanzaBase(self, xmlobj)
		unhandled = True
		for handler in self.__handlers:
			if handler.match(stanza):
				handler.prerun(stanza)
				self.eventqueue.put(('stanza', handler, stanza))
				if handler.checkDelete(): self.__handlers.pop(self.__handlers.index(handler))
				unhandled = False
		if unhandled:
			stanza.unhandled()
			#loop through handlers and test match
			#spawn threads as necessary, call handlers, sending Stanza
	
	def _eventRunner(self):
		logging.debug("Loading event runner")
		while self.run:
			try:
				event = self.eventqueue.get(True, timeout=5)
			except queue.Empty:
				event = None
			if event is not None:
				etype = event[0]
				handler = event[1]
				args = event[2:]
				#etype, handler, *args = event  #python 3.x way
				if etype == 'stanza':
					try:
						handler.run(args[0])
					except Exception as e:
						traceback.print_exc()
						args[0].exception(e)
				elif etype == 'sched':
					try:
						handler.run(*args)
					except:
						logging.error(traceback.format_exc())
				elif etype == 'quit':
					logging.debug("Quitting eventRunner thread")
					return False
	
	def registerHandler(self, handler, before=None, after=None):
		"Add handler with matcher class and parameters."
		self.__handlers.append(handler)
	
	def removeHandler(self, name):
		"Removes the handler."
		idx = 0
		for handler in self.__handlers:
			if handler.name == name:
				self.__handlers.pop(idx)
				return
			idx += 1
	
	def registerStanza(self, stanza_class):
		"Adds stanza.  If root stanzas build stanzas sent in events while non-root stanzas build substanza objects."
		self.__root_stanza.append(stanza_class)
	
	def registerStanzaExtension(self, stanza_class, stanza_extension):
		if stanza_class not in stanza_extensions:
			stanza_extensions[stanza_class] = [stanza_extension]
		else:
			stanza_extensions[stanza_class].append(stanza_extension)
	
	def removeStanza(self, stanza_class, root=False):
		"Removes the stanza's registration."
		if root:
			del self.__root_stanza[stanza_class]
		else:
			del self.__stanza[stanza_class]
	
	def removeStanzaExtension(self, stanza_class, stanza_extension):
		stanza_extension[stanza_class].pop(stanza_extension)

	def tostring(self, xml, xmlns='', stringbuffer=''):
		newoutput = [stringbuffer]
		#TODO respect ET mapped namespaces
		itag = xml.tag.split('}', 1)[-1]
		if '}' in xml.tag:
			ixmlns = xml.tag.split('}', 1)[0][1:]
		else:
			ixmlns = ''
		nsbuffer = ''
		if xmlns != ixmlns and ixmlns != '':
			if ixmlns in self.namespace_map:
				if self.namespace_map[ixmlns] != '':
					itag = "%s:%s" % (self.namespace_map[ixmlns], itag)
			else:
				nsbuffer = """ xmlns="%s\"""" % ixmlns
		newoutput.append("<%s" % itag)
		newoutput.append(nsbuffer)
		for attrib in xml.attrib:
			newoutput.append(""" %s="%s\"""" % (attrib, self.xmlesc(xml.attrib[attrib])))
		if len(xml) or xml.text or xml.tail:
			newoutput.append(">")
			if xml.text:
				newoutput.append(self.xmlesc(xml.text))
			if len(xml):
				for child in xml.getchildren():
					newoutput.append(self.tostring(child, ixmlns))
			newoutput.append("</%s>" % (itag, ))
			if xml.tail:
				newoutput.append(self.xmlesc(xml.tail))
		elif xml.text:
			newoutput.append(">%s</%s>" % (self.xmlesc(xml.text), itag))
		else:
			newoutput.append(" />")
		return ''.join(newoutput)

	def xmlesc(self, text):
		text = list(text)
		cc = 0
		matches = ('&', '<', '"', '>', "'")
		for c in text:
			if c in matches:
				if c == '&':
					text[cc] = '&amp;'
				elif c == '<':
					text[cc] = '&lt;'
				elif c == '>':
					text[cc] = '&gt;'
				elif c == "'":
					text[cc] = '&apos;'
				elif self.escape_quotes:
					text[cc] = '&quot;'
			cc += 1
		return ''.join(text)
	
	def start_stream_handler(self, xml):
		"""Meant to be overridden"""
		pass
