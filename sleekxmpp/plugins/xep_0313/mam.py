"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout,
    Copyright (C) 2017 Mario Hock
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging

import sleekxmpp
from sleekxmpp.stanza import Message, Iq
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.xmlstream.handler import Collector, Waiter, Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.xep_0313 import stanza


log = logging.getLogger(__name__)




class Archive_Query:

    def __init__(
        self, xmpp, start=None, end=None, with_jid=None, continue_after=None,
                 number_of_queried_elements=None, collect_all=True, timeout=None, callback=None):
        self._xmpp = xmpp
        self.timeout = timeout
        self.collect_all = collect_all
        self._callback_ptr = callback

        self._collector = None
        self._cleanup_callback = None

        self._query_id = None
        self._iq = None
        self._last_message = None

        # prepare query
        iq = self._xmpp.Iq()
        self._query_id = iq['id']

        iq['type'] = 'set'
        iq['mam']['queryid'] = self._query_id
        iq['mam']['start'] = start
        iq['mam']['end'] = end
        iq['mam']['with'] = with_jid
        if number_of_queried_elements:
            iq['mam']['rsm']['max'] = number_of_queried_elements
        if continue_after:
            iq['mam']['rsm']['after'] = continue_after

        self._iq = iq

        # program collector
        #    --> collect all archived messages until stopped
        self._collector = Collector(
            'MAM_Results_%s' % self._query_id,
            StanzaPath('message/mam_result@queryid=%s' % self._query_id))
        self._xmpp.register_handler(self._collector)

    def get_id(self):
        return self._query_id
    
    
    def run_blocking(self):
        try:
            complete = False

            while not complete:
                # * send query *
                response = self._iq.send(block=True, timeout=self.timeout)

                # also prepares subsequent query, if necessary
                complete = self.__check_completeness(response)

            response['mam_answer']['results'] = self.__get_results()
            return response

        except XMPPError as e:
            self._collector.stop()
            self._collector = None
            raise e

    def run_async(self, cleanup_callback):
        self._cleanup_callback = cleanup_callback
        self.__send_async_query()

    def __send_async_query(self):
        self._iq.send(
            block=False,
            timeout=self.timeout,
            callback=self.__handle_async_result)

    def __handle_async_result(self, response):
        # this also prepares subsequent query, if necessary
        complete = self.__check_completeness(response)

        # incomplete answer --> get next page
        if not complete:
            self.__send_async_query()

        # * complete answer * --> callback and cleanup
        else:
            response['mam_answer']['results'] = self.__get_results()

            # * callback to application *
            self._callback_ptr(response)
            self._callback_ptr = None

            self._cleanup_callback(self)



    def __check_completeness(self, response):
        """
            NOTE: Also prepares request for next "page"
        """
        if not response["mam_answer"]["complete"]:
            self._last_message = response["mam_answer"]["rsm"]["last"]
            self._iq['mam']['rsm']['after'] = self._last_message

            # answer incomplete
            if self.collect_all:
                return False
            else:
                # quit anyway, as requested
                return True
        else:
            # answer complete
            return True



    def __get_results(self):
        result = self._collector.stop()
        self._collector = None

        return result



class XEP_0313(BasePlugin):

    """
    XEP-0313 Message Archive Management
    """

    name = 'xep_0313'
    description = 'XEP-0313: Message Archive Management'
    dependencies = set(
        ['xep_0004',
         'xep_0030',
         'xep_0050',
         'xep_0059',
         'xep_0297'])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Iq, stanza.MAM)
        register_stanza_plugin(stanza.MAM, self.xmpp['xep_0059'].stanza.Set)
        register_stanza_plugin(Iq, stanza.MAM_Fin)
        register_stanza_plugin(
            stanza.MAM_Fin,
            self.xmpp['xep_0059'].stanza.Set)

        register_stanza_plugin(Iq, stanza.Preferences)
        register_stanza_plugin(Message, stanza.Result)
        register_stanza_plugin(
            stanza.Result,
            self.xmpp['xep_0297'].stanza.Forwarded)

        self._open_queries = {}

    def retrieve(
        self, start=None, end=None, with_jid=None, continue_after=None,
                 number_of_queried_elements=None, collect_all=True, timeout=None, callback=None):

        query = Archive_Query(
            self.xmpp,
            start,
            end,
            with_jid,
            continue_after,
            number_of_queried_elements,
            collect_all,
            timeout,
            callback)
        query_id = query.get_id()

        self._open_queries[query_id] = query

        # Synchronous, blocking (no callback)
        if not callback:
            result = query.run_blocking()
            del self._open_queries[query_id]

            return result

        # Async with callback
        else:
            query.run_async(self.__cleanup_callback)
            

    def __cleanup_callback(self, query):
        del self._open_queries[query.get_id()]
        



    
    
    
    def set_preferences(self, default=None, always=None, never=None,
                        block=True, timeout=None, callback=None):
        """
        The 'default' attribute of the 'prefs' element MUST be one of the following values:

        'always' - all messages are archived by default.
        'never' - messages are never archived by default.
        'roster' - messages are archived only if the contact's bare JID is in the user's roster.
        """

        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['mam_prefs']['default'] = default
        iq['mam_prefs']['always'] = always
        iq['mam_prefs']['never'] = never
        return iq.send(block=block, timeout=timeout, callback=callback)


    def get_preferences(self, block=True, timeout=None, callback=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq["mam_prefs"]

        return iq.send(block=block, timeout=timeout, callback=callback)
