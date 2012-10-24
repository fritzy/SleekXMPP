#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sys
import logging
import getpass
import threading
from optparse import OptionParser

import sleekxmpp
from sleekxmpp.exceptions import XMPPError


# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input


FILE_TYPES = {
    'image/png': 'png',
    'image/gif': 'gif',
    'image/jpeg': 'jpg'
}


class AvatarDownloader(sleekxmpp.ClientXMPP):

    """
    A basic script for downloading the avatars for a user's contacts.
    """

    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start, threaded=True)
        self.add_event_handler("changed_status", self.wait_for_presences)

        self.add_event_handler('vcard_avatar_update', self.on_vcard_avatar)
        self.add_event_handler('avatar_metadata_publish', self.on_avatar)

        self.received = set()
        self.presences_received = threading.Event()

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

        print('Waiting for presence updates...\n')
        self.presences_received.wait(15)
        self.disconnect(wait=True)

    def on_vcard_avatar(self, pres):
        print("Received vCard avatar update from %s" % pres['from'].bare)
        try:
            result = self['xep_0054'].get_vcard(pres['from'], cached=True)
        except XMPPError:
            print("Error retrieving avatar for %s" % pres['from'])
            return
        avatar = result['vcard_temp']['PHOTO']

        filetype = FILE_TYPES.get(avatar['TYPE'], 'png')
        filename = 'vcard_avatar_%s_%s.%s' % (
                pres['from'].bare,
                pres['vcard_temp_update']['photo'],
                filetype)
        with open(filename, 'w+') as img:
            img.write(avatar['BINVAL'])

    def on_avatar(self, msg):
        print("Received avatar update from %s" % msg['from'])
        metadata = msg['pubsub_event']['items']['item']['avatar_metadata']
        for info in metadata['items']:
            if not info['url']:
                try:
                    result = self['xep_0084'].retrieve_avatar(msg['from'], info['id'])
                except XMPPError:
                    print("Error retrieving avatar for %s" % msg['from'])
                    return

                avatar = result['pubsub']['items']['item']['avatar_data']

                filetype = FILE_TYPES.get(metadata['type'], 'png')
                filename = 'avatar_%s_%s.%s' % (msg['from'].bare, info['id'], filetype)
                with open(filename, 'w+') as img:
                    img.write(avatar['value'])
            else:
                # We could retrieve the avatar via HTTP, etc here instead.
                pass

    def wait_for_presences(self, pres):
        """
        Wait to receive updates from all roster contacts.
        """
        self.received.add(pres['from'].bare)
        if len(self.received) >= len(self.client_roster.keys()):
            self.presences_received.set()
        else:
            self.presences_received.clear()


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()
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

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")

    xmpp = AvatarDownloader(opts.jid, opts.password)
    xmpp.register_plugin('xep_0054')
    xmpp.register_plugin('xep_0153')
    xmpp.register_plugin('xep_0084')

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
