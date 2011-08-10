from xml.etree import cElementTree as ET

class OptionalSetting(object):
	interfaces = set(('required',))

	def setRequired(self, value):
		value = bool(value)
		if value and not self['required']:
			self.xml.append(ET.Element("{%s}required" % self.namespace))
		elif not value and self['required']:
			self.delRequired()
	
	def getRequired(self):
		required = self.xml.find("{%s}required" % self.namespace)
		if required is not None:
			return True
		else:
			return False
	
	def delRequired(self):
		required = self.xml.find("{%s}required" % self.namespace)
		if required is not None:
			self.xml.remove(required)

