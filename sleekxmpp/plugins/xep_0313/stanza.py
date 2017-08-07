"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout,
    Copyright (C) 2017 Mario Hock
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import datetime as dt

from sleekxmpp.jid import JID
from sleekxmpp.xmlstream import ElementBase, ET
from sleekxmpp.plugins import xep_0082, xep_0004


class MAM(ElementBase):
    name = 'query'
    namespace = 'urn:xmpp:mam:2'
    plugin_attrib = 'mam'
    interfaces = set(['queryid', 'start', 'end', 'with'])
    sub_interfaces = set(['start', 'end', 'with'])

    def setup(self, xml=None):
        ElementBase.setup(self, xml)
        self._results = []
        self._limiting_results_form = None

    def _get_limiting_results_form(self):
        if not self._limiting_results_form:
            ## FIXME, how to load such a plugin propperly??
            form = xep_0004.XEP_0004(None).make_form(ftype="submit") 
            form.add_field(var="FORM_TYPE", ftype="hidden", value="urn:xmpp:mam:2")
            self.append(form)
            self._limiting_results_form = form

        return self._limiting_results_form



    def get_start(self):
        raise Exception("not implemented")
        return None


    def set_start(self, value):
        if isinstance(value, dt.datetime):
            value = xep_0082.format_datetime(value)

        self._get_limiting_results_form().add_field(
            var="start", ftype="text-single", value=value)


    def get_end(self):
        raise Exception("not implemented")
        return None


    def set_end(self, value):
        if isinstance(value, dt.datetime):
            value = xep_0082.format_datetime(value)

        self._get_limiting_results_form().add_field(
            var="end", ftype="text-single", value=value)

    def get_with(self):
        raise Exception("not implemented")
        return None

    # FIXME, seems that _no_ messages are returned at all, if this is set,
    # though, the generated XML looks fine..
    def set_with(self, value):
        self._get_limiting_results_form().add_field(
            var="with", ftype="jid-single", value=str(value))


class Preferences(ElementBase):
    name = 'prefs'
    namespace = 'urn:xmpp:mam:2'
    plugin_attrib = 'mam_prefs'
    interfaces = set(['default', 'always', 'never'])
    sub_interfaces = set(['always', 'never'])

    def get_always(self):
        results = set()

        jids = self.xml.findall('{%s}always/{%s}jid' % (
            self.namespace, self.namespace))

        for jid in jids:
            results.add(JID(jid.text))

        return results

    def set_always(self, value):
        self._set_sub_text('always', '', keep=True)
        always = self.xml.find('{%s}always' % self.namespace)
        always.clear()

        if not isinstance(value, (list, set)):
            value = [value]

        for jid in value:
            jid_xml = ET.Element('{%s}jid' % self.namespace)
            jid_xml.text = str(jid)
            always.append(jid_xml)

    def get_never(self):
        results = set()

        jids = self.xml.findall('{%s}never/{%s}jid' % (
            self.namespace, self.namespace))

        for jid in jids:
            results.add(JID(jid.text))

        return results

    def set_never(self, value):
        self._set_sub_text('never', '', keep=True)
        never = self.xml.find('{%s}never' % self.namespace)
        never.clear()

        if not isinstance(value, (list, set)):
            value = [value]

        for jid in value:
            jid_xml = ET.Element('{%s}jid' % self.namespace)
            jid_xml.text = str(jid)
            never.append(jid_xml)


class Result(ElementBase):
    name = 'result'
    namespace = 'urn:xmpp:mam:2'
    plugin_attrib = 'mam_result'
    interfaces = set(['queryid', 'id'])



class MAM_Fin(ElementBase):
    name = 'fin'
    namespace = 'urn:xmpp:mam:2'
    plugin_attrib = 'mam_answer'
    interfaces = set(['queryid', 'complete', 'results'])


    # The results interface is meant only as an easy
    # way to access the set of collected message responses
    # from the query.
    def get_results(self):
        return self._results

    def set_results(self, values):
        self._results = values

    def del_results(self):
        self._results = []

