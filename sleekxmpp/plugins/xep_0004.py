"""
	SleekXMPP: The Sleek XMPP Library
	Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
	This file is part of SleekXMPP.

	See the file LICENSE for copying permission.
"""

import logging
import copy
from . import base
from .. xmlstream.handler.callback import Callback
from .. xmlstream.matcher.xpath import MatchXPath
from .. xmlstream.stanzabase import registerStanzaPlugin, ElementBase, ET, JID
from .. stanza.message import Message
import types


log = logging.getLogger(__name__)


class Form(ElementBase):
	namespace = 'jabber:x:data'
	name = 'x'
	plugin_attrib = 'form'
	interfaces = set(('fields', 'instructions', 'items', 'reported', 'title', 'type', 'values'))
	sub_interfaces = set(('title',))
	form_types = set(('cancel', 'form', 'result', 'submit'))

	def __init__(self, *args, **kwargs):
		title = None
		if 'title' in kwargs:
			title = kwargs['title']
			del kwargs['title']
		ElementBase.__init__(self, *args, **kwargs)
		if title is not None:
			self['title'] = title
		self.field = FieldAccessor(self)

	def setup(self, xml=None):
		if ElementBase.setup(self, xml): #if we had to generate xml
			self['type'] = 'form'

	def addField(self, var='', ftype=None, label='', desc='', required=False, value=None, options=None, **kwargs):
		kwtype = kwargs.get('type', None)
		if kwtype is None:
			kwtype = ftype

		field = FormField(parent=self)
		field['var'] = var
		field['type'] = kwtype
		field['label'] = label
		field['desc'] = desc
		field['required'] = required
		field['value'] = value
		if options is not None:
			field['options'] = options
		return field

	def getXML(self, type='submit'):
		log.warning("Form.getXML() is deprecated API compatibility with plugins/old_0004.py")
		return self.xml

	def fromXML(self, xml):
		log.warning("Form.fromXML() is deprecated API compatibility with plugins/old_0004.py")
		n = Form(xml=xml)
		return n

	def addItem(self, values):
		itemXML = ET.Element('{%s}item' % self.namespace)
		self.xml.append(itemXML)
		reported_vars = self['reported'].keys()
		for var in reported_vars:
			fieldXML = ET.Element('{%s}field' % FormField.namespace)
			itemXML.append(fieldXML)
			field = FormField(xml=fieldXML)
			field['var'] = var
			field['value'] = values.get(var, None)

	def addReported(self, var, ftype=None, label='', desc='', **kwargs):
		kwtype = kwargs.get('type', None)
		if kwtype is None:
			kwtype = ftype
		reported = self.xml.find('{%s}reported' % self.namespace)
		if reported is None:
			reported = ET.Element('{%s}reported' % self.namespace)
			self.xml.append(reported)
		fieldXML = ET.Element('{%s}field' % FormField.namespace)
		reported.append(fieldXML)
		field = FormField(xml=fieldXML)
		field['var'] = var
		field['type'] = kwtype
		field['label'] = label
		field['desc'] = desc
		return field

	def cancel(self):
		self['type'] = 'cancel'

	def delFields(self):
		fieldsXML = self.xml.findall('{%s}field' % FormField.namespace)
		for fieldXML in fieldsXML:
			self.xml.remove(fieldXML)

	def delInstructions(self):
		instsXML = self.xml.findall('{%s}instructions')
		for instXML in instsXML:
			self.xml.remove(instXML)

	def delItems(self):
		itemsXML = self.xml.find('{%s}item' % self.namespace)
		for itemXML in itemsXML:
			self.xml.remove(itemXML)

	def delReported(self):
		reportedXML = self.xml.find('{%s}reported' % self.namespace)
		if reportedXML is not None:
			self.xml.remove(reportedXML)

	def getFields(self, use_dict=False):
		fields = {} if use_dict else []
		fieldsXML = self.xml.findall('{%s}field' % FormField.namespace)
		for fieldXML in fieldsXML:
			field = FormField(xml=fieldXML)
			if use_dict:
				fields[field['var']] = field
			else:
				fields.append((field['var'], field))
		return fields

	def getInstructions(self):
		instructions = ''
		instsXML = self.xml.findall('{%s}instructions' % self.namespace)
		return "\n".join([instXML.text for instXML in instsXML])

	def getItems(self):
		items = []
		itemsXML = self.xml.findall('{%s}item' % self.namespace)
		for itemXML in itemsXML:
			item = {}
			fieldsXML = itemXML.findall('{%s}field' % FormField.namespace)
			for fieldXML in fieldsXML:
				field = FormField(xml=fieldXML)
				item[field['var']] = field['value']
			items.append(item)
		return items

	def getReported(self):
		fields = {}
		fieldsXML = self.xml.findall('{%s}reported/{%s}field' % (self.namespace,
									 FormField.namespace))
		for fieldXML in fieldsXML:
			field = FormField(xml=fieldXML)
			fields[field['var']] = field
		return fields

	def getValues(self):
		values = {}
		fields = self.getFields(use_dict=True)
		for var in fields:
			values[var] = fields[var]['value']
		return values

	def reply(self):
		if self['type'] == 'form':
			self['type'] = 'submit'
		elif self['type'] == 'submit':
			self['type'] = 'result'

	def setFields(self, fields, default=None):
		del self['fields']
		for field_data in fields:
			var = field_data[0]
			field = field_data[1]
			field['var'] = var

			self.addField(**field)

	def setInstructions(self, instructions):
		del self['instructions']
		if instructions in [None, '']:
			return
		instructions = instructions.split('\n')
		for instruction in instructions:
			inst = ET.Element('{%s}instructions' % self.namespace)
			inst.text = instruction
			self.xml.append(inst)

	def setItems(self, items):
		for item in items:
			self.addItem(item)

	def setReported(self, reported, default=None):
		for var in reported:
			field = reported[var]
			field['var'] = var
			self.addReported(var, **field)

	def setValues(self, values):
		fields = self.getFields(use_dict=True)
		for field in values:
			fields[field]['value'] = values[field]

	def merge(self, other):
		new = copy.copy(self)
		if type(other) == types.DictType:
			new.setValues(other)
			return new
		nfields = new.getFields(use_dict=True)
		ofields = other.getFields(use_dict=True)
		nfields.update(ofields)
		new.setFields([(x, nfields[x]) for x in nfields])
		return new

class FieldAccessor(object):
	def __init__(self, form):
		self.form = form

	def __getitem__(self, key):
		return self.form.getFields(use_dict=True)[key]

	def __contains__(self, key):
		return key in self.form.getFields(use_dict=True)

	def has_key(self, key):
		return key in self.form.getFields(use_dict=True)


class FormField(ElementBase):
	namespace = 'jabber:x:data'
	name = 'field'
	plugin_attrib = 'field'
	interfaces = set(('answer', 'desc', 'required', 'value', 'options', 'label', 'type', 'var'))
	sub_interfaces = set(('desc',))
	field_types = set(('boolean', 'fixed', 'hidden', 'jid-multi', 'jid-single', 'list-multi',
			   'list-single', 'text-multi', 'text-private', 'text-single'))
	multi_value_types = set(('hidden', 'jid-multi', 'list-multi', 'text-multi'))
	multi_line_types = set(('hidden', 'text-multi'))
	option_types = set(('list-multi', 'list-single'))
	true_values = set((True, '1', 'true'))

	def addOption(self, label='', value=''):
		if self['type'] in self.option_types:
			opt = FieldOption(parent=self)
			opt['label'] = label
			opt['value'] = value
		else:
			raise ValueError("Cannot add options to a %s field." % self['type'])

	def delOptions(self):
		optsXML = self.xml.findall('{%s}option' % self.namespace)
		for optXML in optsXML:
			self.xml.remove(optXML)

	def delRequired(self):
		reqXML = self.xml.find('{%s}required' % self.namespace)
		if reqXML is not None:
			self.xml.remove(reqXML)

	def delValue(self):
		valsXML = self.xml.findall('{%s}value' % self.namespace)
		for valXML in valsXML:
			self.xml.remove(valXML)

	def getAnswer(self):
		return self.getValue()

	def getOptions(self):
		options = []
		optsXML = self.xml.findall('{%s}option' % self.namespace)
		for optXML in optsXML:
			opt = FieldOption(xml=optXML)
			options.append({'label': opt['label'], 'value':opt['value']})
		return options

	def getRequired(self):
		reqXML = self.xml.find('{%s}required' % self.namespace)
		return reqXML is not None

	def getValue(self):
		valsXML = self.xml.findall('{%s}value' % self.namespace)
		if len(valsXML) == 0:
			return None
		elif self['type'] == 'boolean':
			return valsXML[0].text in self.true_values
		elif self['type'] in self.multi_value_types:
			values = []
			for valXML in valsXML:
				if valXML.text is None:
					valXML.text = ''
				values.append(valXML.text)
			if self['type'] == 'text-multi':
				values = "\n".join(values)
			return values
		else:
			return valsXML[0].text

	def setAnswer(self, answer):
		self.setValue(answer)

	def setFalse(self):
		self.setValue(False)

	def setOptions(self, options):
		for value in options:
			if isinstance(value, dict):
				self.addOption(**value)
			else:
				self.addOption(value=value)

	def setRequired(self, required):
		exists = self.getRequired()
		if not exists and required:
			self.xml.append(ET.Element('{%s}required' % self.namespace))
		elif exists and not required:
			self.delRequired()

	def setTrue(self):
		self.setValue(True)

	def setValue(self, value):
		self.delValue()
		valXMLName = '{%s}value' % self.namespace

		if self['type'] == 'boolean':
			if value in self.true_values:
				valXML = ET.Element(valXMLName)
				valXML.text = '1'
				self.xml.append(valXML)
			else:
				valXML = ET.Element(valXMLName)
				valXML.text = '0'
				self.xml.append(valXML)
		elif self['type'] in self.multi_value_types or self['type'] in ['', None]:
			if self['type'] in self.multi_line_types and isinstance(value, str):
				value = value.split('\n')
			if not isinstance(value, list):
				value = [value]
			for val in value:
				if self['type'] in ['', None] and val in self.true_values:
					val = '1'
				valXML = ET.Element(valXMLName)
				valXML.text = val
				self.xml.append(valXML)
		else:
			if isinstance(value, list):
				raise ValueError("Cannot add multiple values to a %s field." % self['type'])
			valXML = ET.Element(valXMLName)
			valXML.text = value
			self.xml.append(valXML)


class FieldOption(ElementBase):
	namespace = 'jabber:x:data'
	name = 'option'
	plugin_attrib = 'option'
	interfaces = set(('label', 'value'))
	sub_interfaces = set(('value',))


class xep_0004(base.base_plugin):
	"""
	XEP-0004: Data Forms
	"""

	def plugin_init(self):
		self.xep = '0004'
		self.description = 'Data Forms'

		self.xmpp.registerHandler(
			Callback('Data Form',
				 MatchXPath('{%s}message/{%s}x' % (self.xmpp.default_ns,
								   Form.namespace)),
				 self.handle_form))

		registerStanzaPlugin(FormField, FieldOption)
		registerStanzaPlugin(Form, FormField)
		registerStanzaPlugin(Message, Form)

	def makeForm(self, ftype='form', title='', instructions=''):
		f = Form()
		f['type'] = ftype
		f['title'] = title
		f['instructions'] = instructions
		return f

	def post_init(self):
		base.base_plugin.post_init(self)
		self.xmpp.plugin['xep_0030'].add_feature('jabber:x:data')

	def handle_form(self, message):
		self.xmpp.event("message_xform", message)

	def buildForm(self, xml):
		return Form(xml=xml)
