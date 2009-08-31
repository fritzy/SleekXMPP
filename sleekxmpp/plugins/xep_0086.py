
from __future__ import with_statement
from . import base
import logging
from xml.etree import cElementTree as ET
import copy

class xep_0086(base.base_plugin):
	"""
	XEP-0086 Error Condition Mappings
	"""

	def plugin_init(self):
		self.xep = '0086'
		self.description = 'Error Condition Mappings'
		self.error_map = {
			'bad-request':('modify','400'),
			'conflict':('cancel','409'),
			'feature-not-implemented':('cancel','501'),
			'forbidden':('auth','403'),
			'gone':('modify','302'),
			'internal-server-error':('wait','500'),
			'item-not-found':('cancel','404'),
			'jid-malformed':('modify','400'),
			'not-acceptable':('modify','406'),
			'not-allowed':('cancel','405'),
			'not-authorized':('auth','401'),
			'payment-required':('auth','402'),
			'recipient-unavailable':('wait','404'),
			'redirect':('modify','302'),
			'registration-required':('auth','407'),
			'remote-server-not-found':('cancel','404'),
			'remote-server-timeout':('wait','504'),
			'resource-constraint':('wait','500'),
			'service-unavailable':('cancel','503'),
			'subscription-required':('auth','407'),
			'undefined-condition':(None,'500'),
			'unexpected-request':('wait','400')
			}


	def makeError(self, condition, cdata=None, errorType=None, text=None, customElem=None):
		conditionElem = self.xmpp.makeStanzaErrorCondition(condition, cdata)
		if errorType is None:
			error = self.xmpp.makeStanzaError(conditionElem, self.error_map[condition][0], self.error_map[condition][1], text, customElem)
		else:
			error = self.xmpp.makeStanzaError(conditionElem, errorType, self.error_map[condition][1], text, customElem)
		error.append(conditionElem)
		return error
