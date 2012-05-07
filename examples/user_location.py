#!/usr/bin/env python

import sys
import logging
import getpass
from optparse import OptionParser

try:
    import json
except ImportError:
    import simplejson as json

try:
    import requests
except ImportError:
    print('This demo requires the requests package for using HTTP.')
    sys.exit()

from sleekxmpp import ClientXMPP


class LocationBot(ClientXMPP):

    def __init__(self, jid, password):
        super(LocationBot, self).__init__(jid, password)

        self.add_event_handler('session_start', self.start, threaded=True)
        self.add_event_handler('user_location_publish', 
                               self.user_location_publish)

        self.register_plugin('xep_0004')
        self.register_plugin('xep_0030')
        self.register_plugin('xep_0060')
        self.register_plugin('xep_0115')
        self.register_plugin('xep_0128')
        self.register_plugin('xep_0163')
        self.register_plugin('xep_0080')

        self.current_tune = None

    def start(self, event):
        self.send_presence()
        self.get_roster()
        self['xep_0115'].update_caps()

        print("Using freegeoip.net to get geolocation.")
        r = requests.get('http://freegeoip.net/json/')
        try:
            data = json.loads(r.text)
        except:
            print("Could not retrieve user location.")
            self.disconnect()
            return

        self['xep_0080'].publish_location(
                lat=data['latitude'],
                lon=data['longitude'],
                locality=data['city'],
                region=data['region_name'],
                country=data['country_name'],
                countrycode=data['country_code'],
                postalcode=data['zipcode'])

    def user_location_publish(self, msg):
        geo = msg['pubsub_event']['items']['item']['geoloc']
        print("%s is at:" % msg['from'])
        for key, val in geo.values.items():
            if val:
                print("  %s: %s" % (key, val))


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

    xmpp = LocationBot(opts.jid, opts.password)

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
