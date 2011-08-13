====================
SleekXMPP Quickstart
====================

.. note::
    
    If you have any issues working through this quickstart guide
    or the other tutorials here, please either send a message to the
    `mailing list <http://groups.google.com/group/sleekxmpp-discussion>`_
    or join the chat room at `sleek@conference.jabber.org
    <xmpp:sleek@conference.jabber.org?join>`_.

If you have not yet installed SleekXMPP, do so now by either checking out a version
from `Github <http://github.com/fritzy/SleekXMPP>`_, or installing it using ``pip``
or ``easy_install``.

.. code-block:: sh

    pip install sleekxmpp  # Or: easy_install sleekxmpp


As a basic starting project, we will create an echo bot which will reply to any
messages sent to it. We also go through adding some basic command line configuration
for enabling or disabling debug log outputs and setting the username and password
for the bot.

For the command line options processing, we will use the built-in ``optparse``
module and the ``getpass`` module for reading in passwords.

TL;DR Just Give me the Boilerplate
----------------------------------
As you wish: :ref:`the completed example <echobot_complete>`.

Overview
--------

To get started, here is a brief outline of the structure that the final project will have:

.. code-block:: python

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    import sys
    import logging
    import getpass
    from optparse import OptionParser

    import sleekxmpp

    '''Here we will create out echo bot class'''

    if __name__ == '__main__':
        '''Here we will configure and read command line options'''

        '''Here we will instantiate our echo bot'''

        '''Finally, we connect the bot and start listening for messages'''

Creating the EchoBot Class
--------------------------

There are three main types of entities within XMPP — servers, components, and
clients. Since our echo bot will only be responding to a few people, and won't need
to remember thousands of users, we will use a client connection. A client connection
is the same type that you use with your standard IM client such as Pidgin or Psi.

SleekXMPP comes with a :class:`ClientXMPP <sleekxmpp.clientxmpp.ClientXMPP>` class
which we can extend to add our message echoing feature. :class:`ClientXMPP <sleekxmpp.clientxmpp.ClientXMPP>`
requires the parameters ``jid`` and ``password``, so we will let our ``EchoBot`` class accept those
as well.

.. code-block:: python

    class EchoBot(sleekxmpp.ClientXMPP):
        
        def __init__(self, jid, password):
            super(EchoBot, self).__init__(jid, password)

Handling Session Start
~~~~~~~~~~~~~~~~~~~~~~
The XMPP spec requires clients to broadcast its presence and retrieve its roster (buddy list) once
it connects and establishes a session with the XMPP server. Until these two tasks are completed,
some servers may not deliver or send messages or presence notifications to the client. So we now
need to be sure that we retrieve our roster and send an initial presence once the session has 
started. To do that, we will register an event handler for the :term:`session_start` event.

.. code-block:: python

     def __init__(self, jid, password):
        super(EchoBot, self).__init__(jid, password)

        self.add_event_handler('session_start', self.start)


Since we want the method ``self.start`` to execute when the :term:`session_start` event is triggered,
we also need to define the ``self.start`` handler.

.. code-block:: python

    def start(self, event):
        self.send_presence()
        self.get_roster()

.. warning::

    Not sending an initial presence and retrieving the roster when using a client instance can
    prevent your program from receiving presence notifications or messages depending on the
    XMPP server you have chosen.

Our event handler, like every event handler, accepts a single parameter which typically is the stanza
that was received that caused the event. In this case, ``event`` will just be an empty dictionary since
there is no associated data.

Our first task of sending an initial presence is done using :meth:`send_presence <sleekxmpp.basexmpp.BaseXMPP.send_presence>`.
Calling :meth:`send_presence <sleekxmpp.basexmpp.BaseXMPP.send_presence>` without any arguments will send the simplest
stanza allowed in XMPP:

.. code-block:: xml

    <presence />


The second requirement is fulfilled using :meth:`get_roster <sleekxmpp.clientxmpp.ClientXMPP.get_roster>`, which
will send an IQ stanza requesting the roster to the server and then wait for the response. You may be wondering
what :meth:`get_roster <sleekxmpp.clientxmpp.ClientXMPP.get_roster>` returns since we are not saving any return
value. The roster data is saved by an internal handler to ``self.roster``, and in the case of a :class:`ClientXMPP
<sleekxmpp.clientxmpp.ClientXMPP>` instance to ``self.client_roster``. (The difference between ``self.roster`` and
``self.client_roster`` is that ``self.roster`` supports storing roster information for multiple JIDs, which is useful
for components, whereas ``self.client_roster`` stores roster data for just the client's JID.)

It is possible for a timeout to occur while waiting for the server to respond, which can happen if the
network is excessively slow or the server is no longer responding. In that case, an :class:`IQTimeout
<sleekxmpp.exceptions.IQTimeout>` is raised. Similarly, an :class:`IQError <sleekxmpp.exceptions.IQError>` exception can
be raised if the request contained bad data or requested the roster for the wrong user. In either case, you can wrap the
``get_roster()`` call in a ``try``/``except`` block to retry the roster retrieval process.

The XMPP stanzas from the roster retrieval process could look like this:

.. code-block:: xml

    <iq type="get">
      <query xmlns="jabber:iq:roster" />
    </iq>

    <iq type="result" to="echobot@example.com" from="example.com">
      <query xmlns="jabber:iq:roster">
        <item jid="friend@example.com" subscription="both" />
      </query>
    </iq>

Responding to Messages
~~~~~~~~~~~~~~~~~~~~~~
Now that an ``EchoBot`` instance handles :term:`session_start`, we can begin receiving and responding
to messages. The :term:`message` event is fired whenever a ``<message />`` stanza is received, including
for group chat messages, errors, etc. Properly responding to messages thus requires checking the ``'type'``
interface of the message :term:`stanza object`.

    
.. _echobot_complete:

The Final Product
-----------------
Here then is the final result you should have after working through the guide above.

.. code-block:: python

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    import sys
    import logging
    import time
    import getpass
    from optparse import OptionParser

    import sleekxmpp

    # Python versions before 3.0 do not use UTF-8 encoding
    # by default. To ensure that Unicode is handled properly
    # throughout SleekXMPP, we will set the default encoding
    # ourselves to UTF-8.
    if sys.version_info < (3, 0):
        reload(sys)
        sys.setdefaultencoding('utf8')


    class EchoBot(sleekxmpp.ClientXMPP):

        """
        A simple SleekXMPP bot that will echo messages it
        receives, along with a short thank you message.
        """

        def __init__(self, jid, password):
            sleekxmpp.ClientXMPP.__init__(self, jid, password)

            # The session_start event will be triggered when
            # the bot establishes its connection with the server
            # and the XML streams are ready for use. We want to
            # listen for this event so that we we can intialize
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
            requesting the roster and broadcasting an intial
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

        # Setup the EchoBot and register plugins. Note that while plugins may
        # have interdependencies, the order in which you register them does
        # not matter.
        xmpp = EchoBot(opts.jid, opts.password)
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0004') # Data Forms
        xmpp.register_plugin('xep_0060') # PubSub
        xmpp.register_plugin('xep_0199') # XMPP Ping

        # If you are working with an OpenFire server, you may need
        # to adjust the SSL version used:
        # xmpp.ssl_version = ssl.PROTOCOL_SSLv3

        # If you want to verify the SSL certificates offered by a server:
        # xmpp.ca_certs = "path/to/ca/cert"

        # Connect to the XMPP server and start processing XMPP stanzas.
        if xmpp.connect():
            # If you do not have the pydns library installed, you will need
            # to manually specify the name of the server if it does not match
            # the one in the JID. For example, to use Google Talk you would
            # need to use:
            #
            # if xmpp.connect(('talk.google.com', 5222)):
            #     ...
            xmpp.process(threaded=False)
            print("Done")
        else:
            print("Unable to connect.")
