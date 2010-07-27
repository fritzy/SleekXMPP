class JID(object):
	def __init__(self, jid):
		"""Initialize a new jid"""
		self.reset(jid)

	def reset(self, jid):
		"""Start fresh from a new jid string"""
		self._full = self._jid = str(jid)
		self._domain = None
		self._resource = None
		self._user = None
		self._domain = None
		self._bare = None
	
	def __getattr__(self, name):
		"""Handle getting the jid values, using cache if available"""
		if name == 'resource':
			if self._resource is not None: return self._resource
			self._resource = self._jid.split('/', 1)[-1]
			return self._resource
		elif name == 'user':
			if self._user is not None: return self._user
			if '@' in self._jid:
				self._user = self._jid.split('@', 1)[0]
			else:
				self._user = self._user
			return self._user
		elif name in ('server', 'domain'):
			if self._domain is not None: return self._domain
			self._domain = self._jid.split('@', 1)[-1].split('/', 1)[0]
			return self._domain
		elif name == 'full':
			return self._jid
		elif name == 'bare':
			if self._bare is not None: return self._bare
			self._bare = self._jid.split('/', 1)[0]
			return self._bare

	def __setattr__(self, name, value):
		"""Edit a jid by updating it's individual values, resetting by a generated jid in the end"""
		if name in ('resource', 'user', 'domain'):
			object.__setattr__(self, "_%s" % name, value)
			self.regenerate()
		elif name ==  'server':
			self.domain = value
		elif name in ('full', 'jid'):
			self.reset(value)
		elif name == 'bare':
			if '@' in value:
				u, d = value.split('@', 1)
				object.__setattr__(self, "_user", u)
				object.__setattr__(self, "_domain", d)
			else:
				object.__setattr__(self, "_domain", value)
			self.regenerate()
		else:
			object.__setattr__(self, name, value)


	def regenerate(self):
		"""Generate a new jid based on current values, useful after editing"""
		jid = ""
		if self.user: jid = "%s@" % self.user
		jid += self.domain
		if self.resource: jid += "/%s" % self.resource
		self.reset(jid)
	
	def __str__(self):
		return self.full

