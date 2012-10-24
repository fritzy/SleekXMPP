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
from sleekxmpp.exceptions import IqError, IqTimeout


# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input


class Disco(sleekxmpp.ClientXMPP):

    """
    A demonstration for using basic service discovery.

    Send a disco#info and disco#items request to a JID/node combination,
    and print out the results.

    May also request only particular info categories such as just features,
    or just items.
    """

    def __init__(self, jid, password, target_jid, target_node='', get=''):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        # Using service discovery requires the XEP-0030 plugin.
        self.register_plugin('xep_0030')

        self.get = get
        self.target_jid = target_jid
        self.target_node = target_node

        # Values to control which disco entities are reported
        self.info_types = ['', 'all', 'info', 'identities', 'features']
        self.identity_types = ['', 'all', 'info', 'identities']
        self.feature_types = ['', 'all', 'info', 'features']
        self.items_types = ['', 'all', 'items']


        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start, threaded=True)

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        In this case, we send disco#info and disco#items
        stanzas to the requested JID and print the results.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.get_roster()
        self.send_presence()

        try:
            if self.get in self.info_types:
                # By using block=True, the result stanza will be
                # returned. Execution will block until the reply is
                # received. Non-blocking options would be to listen
                # for the disco_info event, or passing a handler
                # function using the callback parameter.
                info = self['xep_0030'].get_info(jid=self.target_jid,
                                                 node=self.target_node,
                                                 block=True)
            elif self.get in self.items_types:
                # The same applies from above. Listen for the
                # disco_items event or pass a callback function
                # if you need to process a non-blocking request.
                items = self['xep_0030'].get_items(jid=self.target_jid,
                                                   node=self.target_node,
                                                   block=True)
            else:
                logging.error("Invalid disco request type.")
                return
        except IqError as e:
            logging.error("Entity returned an error: %s" % e.iq['error']['condition'])
        except IqTimeout:
            logging.error("No response received.")
        else:
            header = 'XMPP Service Discovery: %s' % self.target_jid
            print(header)
            print('-' * len(header))
            if self.target_node != '':
                print('Node: %s' % self.target_node)
                print('-' * len(header))

            if self.get in self.identity_types:
                print('Identities:')
                for identity in info['disco_info']['identities']:
                    print('  - %s' % str(identity))

            if self.get in self.feature_types:
                print('Features:')
                for feature in info['disco_info']['features']:
                    print('  - %s' % feature)

            if self.get in self.items_types:
                print('Items:')
                for item in items['disco_items']['items']:
                    print('  - %s' % str(item))
        finally:
            self.disconnect()


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()
    optp.version = '%%prog 0.1'
    optp.usage = "Usage: %%prog [options] %s <jid> [<node>]" % \
                             'all|info|items|identities|features'

    optp.add_option('-q','--quiet', help='set logging to ERROR',
                    action='store_const',
                    dest='loglevel',
                    const=logging.ERROR,
                    default=logging.ERROR)
    optp.add_option('-d','--debug', help='set logging to DEBUG',
                    action='store_const',
                    dest='loglevel',
                    const=logging.DEBUG,
                    default=logging.ERROR)
    optp.add_option('-v','--verbose', help='set logging to COMM',
                    action='store_const',
                    dest='loglevel',
                    const=5,
                    default=logging.ERROR)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    opts,args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if len(args) < 2:
        optp.print_help()
        exit()

    if len(args) == 2:
        args = (args[0], args[1], '')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")

    # Setup the Disco browser.
    xmpp = Disco(opts.jid, opts.password, args[1], args[2], args[0])

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
    else:
        print("Unable to connect.")
