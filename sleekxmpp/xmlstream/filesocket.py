from socket import _fileobject

class filesocket(_fileobject):

	def read(self, size=-1):
		data = self._sock.recv(size)
		if data is not None:
			return data
