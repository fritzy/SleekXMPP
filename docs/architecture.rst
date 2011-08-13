.. index:: XMLStream, BaseXMPP, ClientXMPP, ComponentXMPP

SleekXMPP Architecture
======================

The core of SleekXMPP is contained in four classes: ``XMLStream``,
``BaseXMPP``, ``ClientXMPP``, and ``ComponentXMPP``. Along side this
stack is a library for working with XML objects that eliminates most
of the tedium of creating/manipulating XML.

.. image:: _static/images/arch_layers.png
    :height: 300px
    :align: center


.. index:: XMLStream

The Foundation: XMLStream
-------------------------
``XMLStream`` is a mostly XMPP-agnostic class whose purpose is to read
and write from a bi-directional XML stream. It also allows for callback
functions to execute when XML matching given patterns is received; these
callbacks are also referred to as :term:`stream handlers <stream handler>`.
The class also provides a basic eventing system which can be triggered
either manually or on a timed schedule.

The Main Threads
~~~~~~~~~~~~~~~~
``XMLStream`` instances run using at least three background threads: the
send thread, the read thread, and the scheduler thread. The send thread is
in charge of monitoring the send queue and writing text to the outgoing
XML stream. The read thread pulls text off of the incoming XML stream and
stores the results in an event queue. The scheduler thread is used to emit
events after a given period of time.

Additionally, the main event processing loop may be executed in its
own thread if SleekXMPP is being used in the background for another
application.

Short-lived threads may also be spawned as requested for threaded
:term:`event handlers <event handler>`.

How XML Text is Turned into Action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To demonstrate the flow of information, let's consider what happens
when this bit of XML is received (with an assumed namespace of
``jabber:client``):

.. code-block:: xml

    <message to="user@example.com" from="friend@example.net">
      <body>Hej!</body>
    </message>


1. **Convert XML strings into objects.**

   Incoming text is parsed and converted into XML objects (using
   ElementTree) which are then wrapped into what are referred to as
   :term:`Stanza objects <stanza object>`. The appropriate class for the
   new object is determined using a map of namespaced element names to
   classes.

   Our incoming XML is thus turned into a ``Message`` :term:`stanza object`
   because the namespaced element name ``{jabber:client}message`` is
   associated with the class ``sleekxmpp.stanza.Message``.

2. **Match stanza objects to callbacks.**

   These objects are then compared against the stored patterns associated
   with the registered callback handlers. For each match, a copy of the
   :term:`stanza object` is paired with a reference to the handler and
   placed into the event queue.

   Our ``Message`` object is thus paired with the message stanza handler
   ``BaseXMPP._handle_message`` to create the tuple::

       ('stanza', stanza_obj, handler)

3. **Process the event queue.**

   The event queue is the heart of SleekXMPP. Nearly every action that
   takes place is first inserted into this queue, whether that be received
   stanzas, custom events, or scheduled events.

   When the stanza is pulled out of the event queue with an associated
   callback, the callback function is executed with the stanza as its only
   parameter.

   .. warning:: 
       The callback, aka :term:`stream handler`, is executed in the main
       processing thread. If the handler blocks, event processing will also
       block.

4. **Raise Custom Events**

   Since a :term:`stream handler` shouldn't block, if extensive processing
   for a stanza is required (such as needing to send and receive an
   ``Iq`` stanza), then custom events must be used. These events are not
   explicitly tied to the incoming XML stream and may be raised at any
   time. Importantly, these events may be handled in their own thread.

   When the event is raised, a copy of the stanza is created for each
   handler registered for the event. In contrast to :term:`stream handlers <stream handler>`, 
   these functions are referred to as :term:`event handlers <event handler>`. 
   Each stanza/handler pair is then put into the event queue.

   .. note::
       It is possible to skip the event queue and process an event immediately
       by using ``direct=True`` when raising the event.

   The code for ``BaseXMPP._handle_message`` follows this pattern, and
   raises a ``'message'`` event::

       self.event('message', msg)

   The event call then places the message object back into the event queue
   paired with an :term:`event handler`::

       ('event', 'message', msg_copy1, custom_event_handler_1)
       ('event', 'message', msg_copy2, custom_evetn_handler_2) 

5. **Process Custom Events**

   The stanza and :term:`event handler` are then pulled from the event
   queue, and the handler is executed, passing the stanza as its only
   argument. If the handler was registered as threaded, then a new thread
   will be spawned for it.

   .. note::
       Events may be raised without needing :term:`stanza objects <stanza object>`. 
       For example, you could use ``self.event('custom', {'a': 'b'})``. 
       You don't even need any arguments: ``self.event('no_parameters')``. 
       However, every event handler MUST accept at least one argument.

   Finally, after a long trek, our message is handed off to the user's
   custom handler in order to do awesome stuff::

       msg.reply()
       msg['body'] = "Hey! This is awesome!"
       msg.send()


.. index:: BaseXMPP, XMLStream

Raising XMPP Awareness: BaseXMPP
--------------------------------
While ``XMLStream`` attempts to shy away from anything too XMPP specific,
``BaseXMPP``'s sole purpose is to provide foundational support for sending
and receiving XMPP stanzas. This support includes registering the basic
message, presence, and iq stanzas, methods for creating and sending
stanzas, and default handlers for incoming messages and keeping track of
presence notifications.

The plugin system for adding new XEP support is also maintained by
``BaseXMPP``.

.. index:: ClientXMPP, BaseXMPP

ClientXMPP
----------
``ClientXMPP`` extends ``BaseXMPP`` with additional logic for connecting to
an XMPP server by performing DNS lookups. It also adds support for stream
features such as STARTTLS and SASL.

.. index:: ComponentXMPP, BaseXMPP

ComponentXMPP
-------------
``ComponentXMPP`` is only a thin layer on top of ``BaseXMPP`` that
implements the component handshake protocol.

.. index::
    double: object; stanza

Stanza Objects: A Brief Look
----------------------------
.. seealso::
    See :ref:`api-stanza-objects` for a more detailed overview.

Almost worthy of their own standalone library, :term:`stanza objects <stanza object>`
are wrappers for XML objects which expose dictionary like interfaces
for manipulating their XML content. For example, consider the XML:

.. code-block:: xml

    <message />

A very plain element to start with, but we can create a :term:`stanza object`
using ``sleekxmpp.stanza.Message`` as so::

    msg = Message(xml=ET.fromstring("<message />"))

The ``Message`` stanza class defines interfaces such as ``'body'`` and
``'to'``, so we can assign values to those interfaces to include new XML
content::

    msg['body'] = "Following so far?"
    msg['to'] = 'user@example.com'

Dumping the XML content of ``msg`` (using ``msg.xml``), we find:

.. code-block:: xml

    <message to="user@example.com">
      <body>Following so far?</body>
    </message>

The process is similar for reading from interfaces and deleting interface
contents. A :term:`stanza object` behaves very similarly to a regular
``dict`` object: you may assign to keys, read from keys, and ``del`` keys.

Stanza interfaces come with built-in behaviours such as adding/removing
attribute and sub element values. However, a lot of the time more custom
logic is needed. This can be provided by defining methods of the form
``get_*``, ``set_*``, and ``del_*`` for any interface which requires custom
behaviour.

Stanza Plugins
~~~~~~~~~~~~~~
Since it is generally possible to embed one XML element inside another,
:term:`stanza objects <stanza object>` may be nested. Nested 
:term:`stanza objects <stanza object>` are referred to as :term:`stanza plugins <stanza plugin>`
or :term:`substanzas <substanza>`.

A :term:`stanza plugin` exposes its own interfaces by adding a new
interface to its parent stanza. To demonstrate, consider these two stanza
class definitions using ``sleekxmpp.xmlstream.ElementBase``:


.. code-block:: python

    class Parent(ElementBase):
        name = "the-parent-xml-element-name"
        namespace = "the-parent-namespace"
        interfaces = set(('foo', 'bar'))

    class Child(ElementBase):
        name = "the-child-xml-element-name"
        namespace = "the-child-namespace"
        plugin_attrib = 'child'
        interfaces = set(('baz',))


If we register the ``Child`` stanza as a plugin of the ``Parent`` stanza as
so, using ``sleekxmpp.xmlstream.register_stanza_plugin``::

    register_stanza_plugin(Parent, Child)

Then we can access content in the child stanza through the parent.
Note that the interface used to access the child stanza is the same as
``Child.plugin_attrib``::

    parent = Parent()
    parent['foo'] = 'a'
    parent['child']['baz'] = 'b'

The above code would produce:

.. code-block:: xml

    <the-parent-xml-element xmlns="the-parent-namespace" foo="a">
      <the-child-xml-element xmlsn="the-child-namespace" baz="b" />
    </the-parent-xml-element>

It is also possible to allow a :term:`substanza` to appear multiple times
by using ``iterable=True`` in the ``register_stanza_plugin`` call. All
iterable :term:`substanzas <substanza>` can be accessed using a standard
``substanzas`` interface.
