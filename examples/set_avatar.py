#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2012  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import os
import sys
import imghdr
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


class AvatarSetter(sleekxmpp.ClientXMPP):

    """
    A basic script for downloading the avatars for a user's contacts.
    """

    def __init__(self, jid, password, filepath):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.add_event_handler("session_start", self.start, threaded=True)

        self.filepath = filepath

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

        avatar_file = None
        try:
            avatar_file = open(os.path.expanduser(self.filepath), 'rb')
        except IOError:
            print('Could not find file: %s' % self.filepath)
            return self.disconnect()

        avatar = avatar_file.read()

        avatar_type = 'image/%s' % imghdr.what('', avatar)
        avatar_id = self['xep_0084'].generate_id(avatar)
        avatar_bytes = len(avatar)

        avatar_file.close()

        used_xep84 = False
        try:
            print('Publish XEP-0084 avatar data')
            self['xep_0084'].publish_avatar(avatar)
            used_xep84 = True
        except XMPPError:
            print('Could not publish XEP-0084 avatar')

        try:
            print('Update vCard with avatar')
            self['xep_0153'].set_avatar(avatar=avatar, mtype=avatar_type)
        except XMPPError:
            print('Could not set vCard avatar')

        if used_xep84:
            try:
                print('Advertise XEP-0084 avatar metadata')
                self['xep_0084'].publish_avatar_metadata([
                    {'id': avatar_id,
                     'type': avatar_type,
                     'bytes': avatar_bytes}
                    # We could advertise multiple avatars to provide
                    # options in image type, source (HTTP vs pubsub),
                    # size, etc.
                    # {'id': ....}
                ])
            except XMPPError:
                print('Could not publish XEP-0084 metadata')

        print('Wait for presence updates to propagate...')
        self.schedule('end', 5, self.disconnect, kwargs={'wait': True})


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
    optp.add_option("-f", "--file", dest="filepath",
                    help="path to the avatar file")
    opts,args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.filepath is None:
        opts.filepath = raw_input("Avatar file location: ")

    xmpp = AvatarSetter(opts.jid, opts.password, opts.filepath)
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
