import xmlstream
import time
import socket
from handler.callback import Callback
from matcher.xpath import MatchXPath

def server():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(('localhost', 5228))
	s.listen(1)
	servers = []
	while True:
		conn, addr = s.accept()
		server = xmlstream.XMLStream(conn, 'localhost', 5228)
		server.registerHandler(Callback('test', MatchXPath('test'), testHandler))
		server.process()
		servers.append(server)

def testHandler(xml):
	print("weeeeeeeee!")

server()
