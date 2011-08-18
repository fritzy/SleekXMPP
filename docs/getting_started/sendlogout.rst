Sign in, Send a Message, and Disconnect
=======================================

.. note::
    
    If you have any issues working through this quickstart guide
    or the other tutorials here, please either send a message to the
    `mailing list <http://groups.google.com/group/sleekxmpp-discussion>`_
    or join the chat room at `sleek@conference.jabber.org
    <xmpp:sleek@conference.jabber.org?join>`_.

A common use case for SleekXMPP is to send one-off messages from
time to time. For example, one use case could be sending out a notice when 
a shell script finishes a task.

We will create our one-shot bot based on the pattern explained in :ref:`echobot`. To
start, we create a client class based on :class:`ClientXMPP <sleekxmpp.clientxmpp.ClientXMPP>` and
register a handler for the :term:`session_start` event. We will also accept parameters
for the JID that will receive our message, and the string content of the message.

.. code-block:: python

    import sleekxmpp


    class SendMsgBot(sleekxmpp.ClientXMPP):
        
        def __init__(self, jid, password, recipient, msg):
            super(SendMsgBot, self).__init__(jid, password)

            self.recipient = recipient
            self.msg = msg

            self.add_event_handler('session_start', self.start)

        def start(self, event):
            self.send_presence()
            self.get_roster()

Note that as in :ref:`echobot`, we need to include send an initial presence and request
the roster. Next, we want to send our message, and to do that we will use :meth:`send_message <sleekxmpp.basexmpp.BaseXMPP.send_message>`.

.. code-block:: python

    def start(self, event):
        self.send_presence()
        self.get_roster()

        self.send_message(mto=self.recipient, mbody=self.msg)

Finally, we need to disconnect the client using :meth:`disconnect <sleekxmpp.xmlstream.XMLStream.disconnect>`.
Now, sent stanzas are placed in a queue to pass them to the send thread. If we were to call
:meth:`disconnect <sleekxmpp.xmlstream.XMLStream.disconnect>` without any parameters, then it is possible
for the client to disconnect before the send queue is processed and the message is actually
sent on the wire. To ensure that our message is processed, we use 
:meth:`disconnect(wait=True) <sleekxmpp.xmlstream.XMLStream.disconnect>`.

.. code-block:: python

    def start(self, event):
        self.send_presence()
        self.get_roster()

        self.send_message(mto=self.recipient, mbody=self.msg)

        self.disconnect(wait=True)

.. warning::

    If you happen to be adding stanzas to the send queue faster than the send thread
    can process them, then :meth:`disconnect(wait=True) <sleekxmpp.xmlstream.XMLStream.disconnect>`
    will block and not disconnect.

Final Product
-------------

.. compound::

    The final step is to create a small runner script for initialising our ``SendMsgBot`` class and adding some
    basic configuration options. By following the basic boilerplate pattern in :ref:`echobot`, we arrive
    at the code below. To experiment with this example, you can use:

    .. code-block:: sh

            python send_client.py -d -j oneshot@example.com -t someone@example.net -m "This is a message"

    which will prompt for the password and then log in, send your message, and then disconnect. To test, open
    your regular IM client with the account you wish to send messages to. When you run the ``send_client.py``
    example and instruct it to send your IM client account a message, you should receive the message you
    gave. If the two JIDs you use also have a mutual presence subscription (they're on each other's buddy lists)
    then you will also see the ``SendMsgBot`` client come online and then go offline.

.. include:: ../../examples/send_client.py
    :literal:
