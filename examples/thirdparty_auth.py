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

try:
    from httplib import HTTPSConnection
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
    from http.client import HTTPSConnection

import sleekxmpp
from sleekxmpp.xmlstream import JID

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input


class ThirdPartyAuthBot(sleekxmpp.ClientXMPP):

    """
    A simple SleekXMPP bot that will echo messages it
    receives, along with a short thank you message.

    This version uses a thirdpary service for authentication,
    such as Facebook or Google.
    """

    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        # The X-GOOGLE-TOKEN mech is ranked lower than PLAIN
        # due to Google only allowing a single SASL attempt per
        # connection. So PLAIN will be used for TLS connections,
        # and X-GOOGLE-TOKEN for non-TLS connections. To use
        # X-GOOGLE-TOKEN with a TLS connection, explicitly select
        # it using:
        #
        # sleekxmpp.ClientXMPP.__init__(self, jid, password,
        #                               sasl_mech="X-GOOGLE-TOKEN")

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
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

    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%(body)s" % msg).send()


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

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")

    
    access_token = None

    # Since documentation on how to work with Google tokens
    # can be difficult to find, we'll demo a basic version
    # here. Note that responses could refer to a Captcha
    # URL that would require a browser.

    # Using Facebook or MSN's custom authentication requires
    # a browser, but the process is the same once a token
    # has been retrieved.

    # Request an access token from Google:
    try:
        conn = HTTPSConnection('www.google.com')
    except:
        print('Could not connect to Google')
        sys.exit()

    params = urlencode({
        'accountType': 'GOOGLE',
        'service': 'mail',
        'Email': JID(opts.jid).bare,
        'Passwd': opts.password
    })
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded' 
    }
    try:
        conn.request('POST', '/accounts/ClientLogin', params, headers)
        resp = conn.getresponse().read()
        data = {}
        for line in resp.split():
            k, v = line.split(b'=', 1)
            data[k] = v
    except Exception as e:
        print('Could not retrieve login data')
        sys.exit()

    if b'SID' not in data:
        print('Required data not found')
        sys.exit()


    params = urlencode({
        'SID': data[b'SID'],
        'LSID': data[b'LSID'],
        'service': 'mail'
    })
    try:
        conn.request('POST', '/accounts/IssueAuthToken', params, headers)
        resp = conn.getresponse()
        data = resp.read().split()
    except:
        print('Could not retrieve auth data')
        sys.exit()

    if not data:
        print('Could not retrieve token')
        sys.exit()

    access_token = data[0]


    # Setup the ThirdPartyAuthBot and register plugins. Note that while plugins
    # may have interdependencies, the order in which you register them does not
    # matter.

    # If using MSN, the JID should be "user@messenger.live.com", which will
    # be overridden on session bind.

    # We're using an access token instead of a password, so we'll use `''` as
    # a password argument filler.

    xmpp = ThirdPartyAuthBot(opts.jid, '')  
    xmpp.credentials['access_token'] = access_token

    # The credentials dictionary is used to provide additional authentication
    # information beyond just a password.
    
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0060') # PubSub

    # MSN will kill connections that have been inactive for even
    # short periods of time. So use pings to keep the session alive;
    # whitespace keepalives do not work.
    xmpp.register_plugin('xep_0199', {'keepalive': True, 'frequency': 60})

    # If you are working with an OpenFire server, you may need
    # to adjust the SSL version used:
    # xmpp.ssl_version = ssl.PROTOCOL_SSLv3

    # If you want to verify the SSL certificates offered by a server:
    # xmpp.ca_certs = "path/to/ca/cert"

    # Connect to the XMPP server and start processing XMPP stanzas.
    # Google only allows one SASL attempt per connection, so in order to 
    # enable the X-GOOGLE-TOKEN mechanism, we'll disable TLS.
    if xmpp.connect(use_tls=False):
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
