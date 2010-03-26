"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from socket import _fileobject
import socket

class filesocket(_fileobject):

	def read(self, size=4096):
		data = self._sock.recv(size)
		if data is not None:
			return data

class Socket26(socket._socketobject):

	def makefile(self, mode='r', bufsize=-1):
		"""makefile([mode[, bufsize]]) -> file object
		Return a regular file object corresponding to the socket.  The mode
		and bufsize arguments are as for the built-in open() function."""
		return filesocket(self._sock, mode, bufsize)

