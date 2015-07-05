#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
optp.add_option("--oldjid", dest="old_jid",
                help="JID of the old account")
optp.add_option("--oldpassword", dest="old_password",
                help="password of the old account")

optp.add_option("--newjid", dest="new_jid",
                help="JID of the old account")
optp.add_option("--newpassword", dest="new_password",
                help="password of the old account")


opts, args = optp.parse_args()

# Setup logging.
logging.basicConfig(level=opts.loglevel,
                    format='%(levelname)-8s %(message)s')

if opts.old_jid is None:
    opts.old_jid = raw_input("Old JID: ")
if opts.old_password is None:
    opts.old_password = getpass.getpass("Old Password: ")

if opts.new_jid is None:
    opts.new_jid = raw_input("New JID: ")
if opts.new_password is None:
    opts.new_password = getpass.getpass("New Password: ")


old_xmpp = sleekxmpp.ClientXMPP(opts.old_jid, opts.old_password)

# If you are connecting to Facebook and wish to use the
# X-FACEBOOK-PLATFORM authentication mechanism, you will need
# your API key and an access token. Then you'll set:
# xmpp.credentials['api_key'] = 'THE_API_KEY'
# xmpp.credentials['access_token'] = 'THE_ACCESS_TOKEN'

# If you are connecting to MSN, then you will need an
# access token, and it does not matter what JID you
# specify other than that the domain is 'messenger.live.com',
# so '_@messenger.live.com' will work. You can specify
# the access token as so:
# xmpp.credentials['access_token'] = 'THE_ACCESS_TOKEN'

# If you are working with an OpenFire server, you may need
# to adjust the SSL version used:
# xmpp.ssl_version = ssl.PROTOCOL_SSLv3

# If you want to verify the SSL certificates offered by a server:
# xmpp.ca_certs = "path/to/ca/cert"

roster = []

def on_session(event):
    roster.append(old_xmpp.get_roster())
    old_xmpp.disconnect()
old_xmpp.add_event_handler('session_start', on_session)

if old_xmpp.connect():
    old_xmpp.process(block=True)

if not roster:
    print('No roster to migrate')
    sys.exit()

new_xmpp = sleekxmpp.ClientXMPP(opts.new_jid, opts.new_password)
def on_session2(event):
    new_xmpp.get_roster()
    new_xmpp.send_presence()

    logging.info(roster[0])
    data = roster[0]['roster']['items']
    logging.info(data)

    for jid, item in data.items():
        if item['subscription'] != 'none':
            new_xmpp.send_presence(ptype='subscribe', pto=jid)
        new_xmpp.update_roster(jid,
                name = item['name'],
                groups = item['groups'])
    new_xmpp.disconnect()
new_xmpp.add_event_handler('session_start', on_session2)

if new_xmpp.connect():
    new_xmpp.process(block=True)
