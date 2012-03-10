#!/usr/bin/env python

import sys
import logging
import getpass
from optparse import OptionParser

try:
    from appscript import *
except ImportError:
    print('This demo requires the appscript package to interact with iTunes.')
    sys.exit()

from sleekxmpp import ClientXMPP


class TuneBot(ClientXMPP):

    def __init__(self, jid, password):
        super(TuneBot, self).__init__(jid, password)

        # Check for the current song every 5 seconds.
        self.schedule('Check Current Tune', 5, self._update_tune, repeat=True)

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('user_tune_publish', self.user_tune_publish)

        self.register_plugin('xep_0004')
        self.register_plugin('xep_0030')
        self.register_plugin('xep_0060')
        self.register_plugin('xep_0115')
        self.register_plugin('xep_0118')
        self.register_plugin('xep_0128')
        self.register_plugin('xep_0163')

        self.current_tune = None

    def start(self, event):
        self.send_presence()
        self.get_roster()
        self['xep_0115'].update_caps()

    def _update_tune(self):
        itunes_count = app('System Events').processes[its.name == 'iTunes'].count()
        if itunes_count > 0:
            iTunes = app('iTunes')
            if iTunes.player_state.get() == k.playing:
                track = iTunes.current_track.get()
                length = track.time.get()
                if ':' in length:
                    minutes, secs = map(int, length.split(':'))
                    secs += minutes * 60
                else:
                    secs = int(length)

                artist = track.artist.get()
                title = track.name.get()
                source = track.album.get()
                rating = track.rating.get() / 10

                tune = (artist, secs, rating, source, title)
                if tune != self.current_tune:
                    self.current_tune = tune

                    # We have a new song playing, so publish it.
                    self['xep_0118'].publish_tune(
                            artist=artist,
                            length=secs,
                            title=title,
                            rating=rating,
                            source=source)
            else:
                # No song is playing, clear the user tune.
                tune = None
                if tune != self.current_tune:
                    self.current_tune = tune
                    self['xep_0118'].stop()

    def user_tune_publish(self, msg):
        tune = msg['pubsub_event']['items']['item']['tune']
        print("%s is listening to: %s" % (msg['from'], tune['title']))


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

    xmpp = TuneBot(opts.jid, opts.password)

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
