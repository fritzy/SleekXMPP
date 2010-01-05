class XMPPError(Exception):
	def __init__(self, condition='undefined-condition', text=None, etype=None, extension=None, extension_ns=None, extension_args=None):
		self.condition = condition
		self.text = text
		self.etype = etype
		self.extension = extension
		self.extension_ns = extension_ns
		self.extension_args = extension_args
