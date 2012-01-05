Following *XMPP: The Definitive Guide*
======================================

SleekXMPP was featured in the first edition of the O'Reilly book 
`XMPP: The Definitive Guide <http://oreilly.com/catalog/9780596521271/>`_
by Peter Saint-Andre, Kevin Smith, and Remko Tronçon. The original source code
for the book's examples can be found at http://github.com/remko/xmpp-tdg. An
updated version of the source code, maintained to stay current with the latest
SleekXMPP release, is available at http://github.com/legastero/xmpp-tdg.

However, since publication, SleekXMPP has advanced from version 0.2.1 to version
1.0 and there have been several major API changes. The most notable is the
introduction of :term:`stanza objects <stanza object>` which have simplified and
standardized interactions with the XMPP XML stream.

What follows is a walk-through of *The Definitive Guide* highlighting the
changes needed to make the code examples work with version 1.0 of SleekXMPP.
These changes have been kept to a minimum to preserve the correlation with
the book's explanations, so be aware that some code may not use current best
practices.

Example 2-2. (Page 26)
----------------------

**Implementation of a basic bot that echoes all incoming messages back to its sender.**

The echo bot example requires a change to the ``handleIncomingMessage`` method
to reflect the use of the ``Message`` :term:`stanza object`. The
``"jid"`` field of the message object should now be ``"from"`` to match the
``from`` attribute of the actual XML message stanza. Likewise, ``"message"``
changes to ``"body"`` to match the ``body`` element of the message stanza.

Updated Code
~~~~~~~~~~~~

.. code-block:: python

    def handleIncomingMessage(self, message):
        self.xmpp.sendMessage(message["from"], message["body"])

`View full source <http://github.com/legastero/xmpp-tdg/blob/master/code/EchoBot/EchoBot.py>`_ |
`View original code <http://github.com/remko/xmpp-tdg/blob/master/code/EchoBot/EchoBot.py>`_

Example 14-1. (Page 215)
------------------------

**CheshiR IM bot implementation.**

The main event handling method in the Bot class is meant to process both message
events and presence update events. With the new changes in SleekXMPP 1.0,
extracting a CheshiR status "message" from both types of stanzas
requires accessing different attributes. In the case of a message stanza, the
``"body"`` attribute would contain the CheshiR message. For a presence event,
the information is stored in the ``"status"`` attribute. To handle both cases,
we can test the type of the given event object and look up the proper attribute
based on the type.

Like in the EchoBot example, the expression ``event["jid"]`` needs to change
to ``event["from"]`` in order to get a JID object for the stanza's sender.
Because other functions in CheshiR assume that the JID is a string, the ``jid``
attribute is used to access the string version of the JID. A check is also added
in case ``user`` is ``None``, but the check could (and probably should) be
placed in ``addMessageFromUser``.

Another change is needed in ``handleMessageAddedToBackend`` where
an HTML-IM response is created. The HTML content should be enclosed in a single
element, such as a ``<p>`` tag.

Updated Code
~~~~~~~~~~~~

.. code-block:: python

  def handleIncomingXMPPEvent(self, event):
    msgLocations = {sleekxmpp.stanza.presence.Presence: "status",
                    sleekxmpp.stanza.message.Message: "body"}

    message = event[msgLocations[type(event)]]
    user = self.backend.getUserFromJID(event["from"].jid)
    if user is not None:
      self.backend.addMessageFromUser(message, user)
  
  def handleMessageAddedToBackend(self, message) :
    body = message.user + ": " + message.text
    htmlBody = "<p><a href='%(uri)s'>%(user)s</a>: %(message)s</p>" % {
      "uri": self.url + "/" + message.user,
      "user" : message.user, "message" : message.text }
    for subscriberJID in self.backend.getSubscriberJIDs(message.user) :
      self.xmpp.sendMessage(subscriberJID, body, mhtml=htmlBody)

`View full source <http://github.com/legastero/xmpp-tdg/blob/master/code/CheshiR/Bot.py>`_ |
`View original code <http://github.com/remko/xmpp-tdg/blob/master/code/CheshiR/Bot.py>`_


Example 14-3. (Page 217)
------------------------
**Configurable CheshiR IM bot implementation.**

.. note::
    Since the CheshiR examples build on each other, see previous sections for
    corrections to code that is not marked as new in the book example.

The main difference for the configurable IM bot is the handling for the
data form in ``handleConfigurationCommand``. The test for equality
with the string ``"1"`` is no longer required; SleekXMPP converts
boolean data form fields to the values ``True`` and ``False``
automatically.

For the method ``handleIncomingXMPPPresence``, the attribute
``"jid"`` is again converted to ``"from"`` to get a JID
object for the presence stanza's sender, and the ``jid`` attribute is
used to access the string version of that JID object. A check is also added in
case ``user`` is ``None``, but the check could (and probably
should) be placed in ``getShouldMonitorPresenceFromUser``.

Updated Code
~~~~~~~~~~~~

.. code-block:: python

  def handleConfigurationCommand(self, form, sessionId):
    values = form.getValues()
    monitorPresence =values["monitorPresence"]
    jid = self.xmpp.plugin["xep_0050"].sessions[sessionId]["jid"]
    user = self.backend.getUserFromJID(jid)
    self.backend.setShouldMonitorPresenceFromUser(user, monitorPresence)

  def handleIncomingXMPPPresence(self, event):
    user = self.backend.getUserFromJID(event["from"].jid)
    if user is not None:
      if self.backend.getShouldMonitorPresenceFromUser(user):
        self.handleIncomingXMPPEvent(event)

`View full source <http://github.com/legastero/xmpp-tdg/blob/master/code/CheshiR/ConfigurableBot.py>`_ |
`View original code <http://github.com/remko/xmpp-tdg/blob/master/code/CheshiR/ConfigurableBot.py>`_


Example 14-4. (Page 220)
------------------------
**CheshiR IM server component implementation.**

.. note::
    Since the CheshiR examples build on each other, see previous sections for
    corrections to code that is not marked as new in the book example.

Like several previous examples, a needed change is to replace
``subscription["from"]`` with ``subscription["from"].jid`` because the
``BaseXMPP`` method ``makePresence`` requires the JID to be a string.

A correction needs to be made in ``handleXMPPPresenceProbe`` because a line was
left out of the original implementation; the variable ``user`` is undefined. The
JID of the user can be extracted from the presence stanza's ``from`` attribute.

Since this implementation of CheshiR uses an XMPP component, it must
include a ``from`` attribute in all messages that it sends. Adding the
``from`` attribute is done by including ``mfrom=self.xmpp.jid`` in calls to
``self.xmpp.sendMessage``.

Updated Code
~~~~~~~~~~~~

.. code-block:: python

  def handleXMPPPresenceProbe(self, event) :
    self.xmpp.sendPresence(pto = event["from"])

  def handleXMPPPresenceSubscription(self, subscription) :
    if subscription["type"] == "subscribe" :
      userJID = subscription["from"].jid
      self.xmpp.sendPresenceSubscription(pto=userJID, ptype="subscribed")
      self.xmpp.sendPresence(pto = userJID)
      self.xmpp.sendPresenceSubscription(pto=userJID, ptype="subscribe")

  def handleMessageAddedToBackend(self, message) :
    body = message.user + ": " + message.text
    for subscriberJID in self.backend.getSubscriberJIDs(message.user) :
      self.xmpp.sendMessage(subscriberJID, body, mfrom=self.xmpp.jid)

`View full source <http://github.com/legastero/xmpp-tdg/blob/master/code/CheshiR/SimpleComponent.py>`_ |
`View original code <http://github.com/remko/xmpp-tdg/blob/master/code/CheshiR/SimpleComponent.py>`_


Example 14-6. (Page 223)
------------------------
**CheshiR IM server component with in-band registration support.**

.. note::
    Since the CheshiR examples build on each other, see previous sections for
    corrections to code that is not marked as new in the book example.

After applying the changes from Example 14-4 above, the registrable component
implementation should work correctly.

.. tip::
    To see how to implement in-band registration as a SleekXMPP plugin,
    see the tutorial :ref:`tutorial-create-plugin`.

`View full source <http://github.com/legastero/xmpp-tdg/blob/master/code/CheshiR/RegistrableComponent.py>`_ |
`View original code <http://github.com/remko/xmpp-tdg/blob/master/code/CheshiR/RegistrableComponent.py>`_

Example 14-7. (Page 225)
------------------------
**Extended CheshiR IM server component implementation.**

.. note::
    Since the CheshiR examples build on each other, see previous 
    sections for corrections to code that is not marked as new in the book
    example.

While the final code example can look daunting with all of the changes
made, it requires very few modifications to work with the latest version of
SleekXMPP. Most differences are the result of CheshiR's backend functions
expecting JIDs to be strings so that they can be stripped to bare JIDs. To
resolve these, use the ``jid`` attribute of the JID objects. Also,
references to ``"message"`` and ``"jid"`` attributes need to
be changed to either ``"body"`` or ``"status"``, and either
``"from"`` or ``"to"`` depending on if the object is a message
or presence stanza and which of the JIDs from the stanza is needed.

Updated Code
~~~~~~~~~~~~

.. code-block:: python

  def handleIncomingXMPPMessage(self, event) :
    message = self.addRecipientToMessage(event["body"], event["to"].jid)
    user = self.backend.getUserFromJID(event["from"].jid)
    self.backend.addMessageFromUser(message, user)

  def handleIncomingXMPPPresence(self, event) :
    if event["to"].jid == self.componentDomain :
      user = self.backend.getUserFromJID(event["from"].jid)
      self.backend.addMessageFromUser(event["status"], user)

  ...

  def handleXMPPPresenceSubscription(self, subscription) :
    if subscription["type"] == "subscribe" :
      userJID = subscription["from"].jid
      user = self.backend.getUserFromJID(userJID)
      contactJID = subscription["to"]
      self.xmpp.sendPresenceSubscription(
          pfrom=contactJID, pto=userJID, ptype="subscribed", pnick=user)
      self.sendPresenceOfContactToUser(contactJID=contactJID, userJID=userJID)
      if contactJID == self.componentDomain :
        self.sendAllContactSubscriptionRequestsToUser(userJID)

`View full source <http://github.com/legastero/xmpp-tdg/blob/master/code/CheshiR/Component.py>`_ |
`View original code <http://github.com/remko/xmpp-tdg/blob/master/code/CheshiR/Component.py>`_ 
