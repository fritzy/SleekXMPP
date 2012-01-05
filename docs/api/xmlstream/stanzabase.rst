.. _stanzabase:

==============
Stanza Objects
==============

.. module:: sleekxmpp.xmlstream.stanzabase

The :mod:`~sleekmxpp.xmlstream.stanzabase` module provides a wrapper for the
standard :mod:`~xml.etree.ElementTree` module that makes working with XML
less painful. Instead of having to manually move up and down an element
tree and insert subelements and attributes, you can interact with an object
that behaves like a normal dictionary or JSON object, which silently maps
keys to XML attributes and elements behind the scenes.

Overview
--------

The usefulness of this layer grows as the XML you have to work with
becomes nested. The base unit here, :class:`ElementBase`, can map to a
single XML element, or several depending on how advanced of a mapping
is desired from interface keys to XML structures. For example, a single
:class:`ElementBase` derived class could easily describe:

.. code-block:: xml

    <message to="user@example.com" from="friend@example.com">
      <body>Hi!</body>
      <x:extra>
        <x:item>Custom item 1</x:item>
        <x:item>Custom item 2</x:item>
        <x:item>Custom item 3</x:item>
      </x:extra>
    </message>

If that chunk of XML were put in the :class:`ElementBase` instance
``msg``, we could extract the data from the XML using::

    >>> msg['extra']
    ['Custom item 1', 'Custom item 2', 'Custom item 3']

Provided we set up the handler for the ``'extra'`` interface to load the
``<x:item>`` element content into a list.

The key concept is that given an XML structure that will be repeatedly
used, we can define a set of :term:`interfaces` which when we read from,
write to, or delete, will automatically manipulate the underlying XML
as needed. In addition, some of these interfaces may in turn reference
child objects which expose interfaces for particularly complex child
elements of the original XML chunk.

.. seealso::
    :ref:`create-stanza-interfaces`.

Because the :mod:`~sleekxmpp.xmlstream.stanzabase` module was developed
as part of an `XMPP <http://xmpp.org>`_ library, these chunks of XML are
referred to as :term:`stanzas <stanza>`, and in SleekXMPP we refer to a
subclass of :class:`ElementBase` which defines the interfaces needed for
interacting with a given :term:`stanza` a :term:`stanza object`.

To make dealing with more complicated and nested :term:`stanzas <stanza>`
or XML chunks easier, :term:`stanza objects <stanza object>` can be
composed in two ways: as iterable child objects or as plugins. Iterable
child stanzas, or :term:`substanzas`, are accessible through a special
``'substanzas'`` interface. This option is useful for stanzas which
may contain more than one of the same kind of element. When there is
only one child element, the plugin method is more useful. For plugins,
a parent stanza object delegates one of its XML child elements to the
plugin stanza object. Here is an example:

.. code-block:: xml

    <iq type="result">
      <query xmlns="http://jabber.org/protocol/disco#info">
        <identity category="client" type="bot" name="SleekXMPP Bot" />
      </query>
    </iq>

We can can arrange this stanza into two objects: an outer, wrapper object for
dealing with the ``<iq />`` element and its attributes, and a plugin object to
control the ``<query />`` payload element. If we give the plugin object the
name ``'disco_info'`` (using its :attr:`ElementBase.plugin_attrib` value), then
we can access the plugin as so::

    >>> iq['disco_info']
    '<query xmlns="http://jabber.org/protocol/disco#info">
      <identity category="client" type="bot" name="SleekXMPP Bot" />
    </query>'

We can then drill down through the plugin object's interfaces as desired::

    >>> iq['disco_info']['identities']
    [('client', 'bot', 'SleekXMPP Bot')]

Plugins may also add new interfaces to the parent stanza object as if they
had been defined by the parent directly, and can also override the behaviour
of an interface defined by the parent.

.. seealso::

    - :ref:`create-stanza-plugins`
    - :ref:`create-extension-plugins`
    - :ref:`override-parent-interfaces`
     

Registering Stanza Plugins
--------------------------

.. autofunction:: register_stanza_plugin

ElementBase
-----------

.. autoclass:: ElementBase
    :members:
    :private-members:
    :special-members:

StanzaBase
----------

.. autoclass:: StanzaBase
    :members:
