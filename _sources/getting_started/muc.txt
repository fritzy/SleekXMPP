.. _mucbot:

=========================
Mulit-User Chat (MUC) Bot
=========================

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


Now that you've got the basic gist of using SleekXMPP by following the
echobot example (:ref:`echobot`), we can use one of the bundled plugins
to create a very popular XMPP starter project: a `Multi-User Chat`_
(MUC) bot. Our bot will login to an XMPP server, join an MUC chat room
and "lurk" indefinitely, responding with a generic message to anyone
that mentions its nickname. It will also greet members as they join the
chat room.

.. _`multi-user chat`: http://xmpp.org/extensions/xep-0045.html

Joining The Room
----------------

As usual, our code will be based on the pattern explained in :ref:`echobot`.
To start, we create an ``MUCBot`` class based on
:class:`ClientXMPP <sleekxmpp.clientxmpp.ClientXMPP>` and which accepts
parameters for the JID of the MUC room to join, and the nick that the
bot will use inside the chat room.  We also register an
:term:`event handler` for the :term:`session_start` event.


.. code-block:: python

    import sleekxmpp

    class MUCBot(sleekxmpp.ClientXMPP):

        def __init__(self, jid, password, room, nick):
            sleekxmpp.ClientXMPP.__init__(self, jid, password)

            self.room = room
            self.nick = nick

            self.add_event_handler("session_start", self.start)

After initialization, we also need to register the MUC (XEP-0045) plugin
so that we can make use of the group chat plugin's methods and events.

.. code-block:: python

    xmpp.register_plugin('xep_0045')

Finally, we can make our bot join the chat room once an XMPP session
has been established:

.. code-block:: python

    def start(self, event):
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        wait=True)

Note that as in :ref:`echobot`, we need to include send an initial presence and request
the roster. Next, we want to join the group chat, so we call the
``joinMUC`` method of the MUC plugin.

.. note::

    The :attr:`plugin <sleekxmpp.basexmpp.BaseXMPP.plugin>` attribute is
    dictionary that maps to instances of plugins that we have previously
    registered, by their names.


Adding Functionality
--------------------

Currently, our bot just sits dormantly inside the chat room, but we
would like it to respond to two distinct events by issuing a generic
message in each case to the chat room. In particular, when a member
mentions the bot's nickname inside the chat room, and when a member
joins the chat room.

Responding to Mentions
~~~~~~~~~~~~~~~~~~~~~~

Whenever a user mentions our bot's nickname in chat, our bot will
respond with a generic message resembling *"I heard that, user."* We do
this by examining all of the messages sent inside the chat and looking
for the ones which contain the nickname string.

First, we register an event handler for the :term:`groupchat_message`
event inside the bot's ``__init__`` function.

.. note::

    We do not register a handler for the :term:`message` event in this
    bot, but if we did, the group chat message would have been sent to
    both handlers.

.. code-block:: python

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)

Then, we can send our generic message whenever the bot's nickname gets
mentioned.

.. warning::

    Always check that a message is not from yourself,
    otherwise you will create an infinite loop responding
    to your own messages.

.. code-block:: python

    def muc_message(self, msg):
        if msg['mucnick'] != self.nick and self.nick in msg['body']:
            self.send_message(mto=msg['from'].bare,
                              mbody="I heard that, %s." % msg['mucnick'],
                              mtype='groupchat')


Greeting Members
~~~~~~~~~~~~~~~~

Now we want to greet member whenever they join the group chat. To
do this we will use the dynamic ``muc::room@server::got_online`` [1]_
event so it's a good idea to register an event handler for it.

.. note::

    The groupchat_presence event is triggered whenever a
    presence stanza is received from any chat room, including
    any presences you send yourself. To limit event handling
    to a single room, use the events ``muc::room@server::presence``,
    ``muc::room@server::got_online``, or ``muc::room@server::got_offline``.

.. code-block:: python

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("muc::%s::got_online" % self.room,
                               self.muc_online)

Now all that's left to do is to greet them:

.. code-block:: python

    def muc_online(self, presence):
        if presence['muc']['nick'] != self.nick:
            self.send_message(mto=presence['from'].bare,
                              mbody="Hello, %s %s" % (presence['muc']['role'],
                                                      presence['muc']['nick']),
                              mtype='groupchat')

.. [1] this is similar to the :term:`got_online` event and is sent by
       the xep_0045 plugin whenever a member joins the referenced
       MUC chat room.


Final Product
-------------

.. compound::

    The final step is to create a small runner script for initialising our ``MUCBot`` class and adding some
    basic configuration options. By following the basic boilerplate pattern in :ref:`echobot`, we arrive
    at the code below. To experiment with this example, you can use:

    .. code-block:: sh

            python muc.py -d -j jid@example.com -r room@muc.example.net -n lurkbot

    which will prompt for the password, log in, and join the group chat. To test, open
    your regular IM client and join the same group chat that you sent the bot to. You
    will see ``lurkbot`` as one of the members in the group chat, and that it greeted
    you upon entry. Send a message with the string "lurkbot" inside the body text, and you
    will also see that it responds with our pre-programmed customized message.

.. include:: ../../examples/muc.py
    :literal:
