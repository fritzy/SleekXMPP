#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sys
import logging
import getpass
from optparse import OptionParser

import sleekxmpp

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input


class CommandUserBot(sleekxmpp.ClientXMPP):

    """
    A simple SleekXMPP bot that uses the adhoc command
    provided by the adhoc_provider.py example.
    """

    def __init__(self, jid, password, other, greeting):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.command_provider = other
        self.greeting = greeting

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.send_presence()
        self.get_roster()

        # We first create a session dictionary containing:
        #   'next'  -- the handler to execute on a successful response
        #   'error' -- the handler to execute if an error occurs

        # The session may also contain custom data.

        session = {'greeting': self.greeting,
                   'next': self._command_start,
                   'error': self._command_error}

        self['xep_0050'].start_command(jid=self.command_provider,
                                       node='greeting',
                                       session=session)

    def message(self, msg):
        """
        Process incoming message stanzas.

        Arguments:
            msg -- The received message stanza.
        """
        logging.info(msg['body'])

    def _command_start(self, iq, session):
        """
        Process the initial command result.

        Arguments:
            iq      -- The iq stanza containing the command result.
            session -- A dictionary of data relevant to the command
                       session. Additional, custom data may be saved
                       here to persist across handler callbacks.
        """

        # The greeting command provides a form with a single field:
        # <x xmlns="jabber:x:data" type="form">
        #   <field var="greeting"
        #          type="text-single"
        #          label="Your greeting" />
        # </x>

        form = self['xep_0004'].makeForm(ftype='submit')
        form.addField(var='greeting',
                      value=session['greeting'])

        session['payload'] = form

        # We don't need to process the next result.
        session['next'] = None

        # Other options include using:
        # continue_command() -- Continue to the next step in the workflow
        # cancel_command()   -- Stop command execution.

        self['xep_0050'].complete_command(session)

    def _command_error(self, iq, session):
        """
        Process an error that occurs during command execution.

        Arguments:
            iq      -- The iq stanza containing the error.
            session -- A dictionary of data relevant to the command
                       session. Additional, custom data may be saved
                       here to persist across handler callbacks.
        """
        logging.error("COMMAND: %s %s" % (iq['error']['condition'],
                                          iq['error']['text']))

        # Terminate the command's execution and clear its session.
        # The session will automatically be cleared if no error
        # handler is provided.
        self['xep_0050'].terminate_command(session)
        self.disconnect()


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-o", "--other", dest="other",
                    help="JID providing commands")
    optp.add_option("-g", "--greeting", dest="greeting",
                    help="Greeting")

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.other is None:
        opts.other = raw_input("JID Providing Commands: ")
    if opts.greeting is None:
        opts.greeting = raw_input("Greeting: ")

    # Setup the CommandBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = CommandUserBot(opts.jid, opts.password, opts.other, opts.greeting)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0050') # Adhoc Commands

    # If you are working with an OpenFire server, you may need
    # to adjust the SSL version used:
    # xmpp.ssl_version = ssl.PROTOCOL_SSLv3

    # If you want to verify the SSL certificates offered by a server:
    # xmpp.ca_certs = "path/to/ca/cert"

    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect():
        # If you do not have the dnspython library installed, you will need
        # to manually specify the name of the server if it does not match
        # the one in the JID. For example, to use Google Talk you would
        # need to use:
        #
        # if xmpp.connect(('talk.google.com', 5222)):
        #     ...
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")
