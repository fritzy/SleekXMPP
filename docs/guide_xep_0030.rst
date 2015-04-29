XEP-0030: Working with Service Discovery
========================================

XMPP networks can be composed of many individual clients, components,
and servers. Determining the JIDs for these entities and the various
features they may support is the role of `XEP-0030, Service
Discovery <http://xmpp.org/extensions/xep-0030.html>`_, or "disco" for short.

Every XMPP entity may possess what are called nodes. A node is just a name for
some aspect of an XMPP entity. For example, if an XMPP entity provides `Ad-Hoc
Commands <http://xmpp.org/extensions/xep-0050.html>`_, then it will have a node
named ``http://jabber.org/protocol/commands`` which will contain information
about the commands provided. Other agents using these ad-hoc commands will
interact with the information provided by this node. Note that the node name is
just an identifier; there is no inherent meaning.

Working with service discovery is about creating and querying these nodes.
According to XEP-0030, a node may contain three types of information:
identities, features, and items. (Further, extensible, information types are
defined in `XEP-0128 <http://xmpp.org/extensions/xep-0128.html>`_, but they are
not yet implemented by SleekXMPP.) SleekXMPP provides methods to configure each
of these node attributes.

Configuring Service Discovery
-----------------------------
The design focus for the XEP-0030 plug-in is handling info and items requests
in a dynamic fashion, allowing for complex policy decisions of who may receive
information and how much, or use alternate backend storage mechanisms for all
of the disco data. To do this, each action that the XEP-0030 plug-in performs
is handed off to what is called a "node handler," which is just a callback
function. These handlers are arranged in a hierarchy that allows for a single
handler to manage an entire domain of JIDs (say for a component), while allowing
other handler functions to override that global behaviour for certain JIDs, or
even further limited to only certain JID and node combinations.

The Dynamic Handler Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* ``global``: (JID is None, node is None)

  Handlers assigned at this level for an action (such as ``add_feature``) provide a global default
  behaviour when the action is performed.

* ``jid``: (JID assigned, node is None)

  At this level, handlers provide a default behaviour for actions affecting any node owned by the
  JID in question. This level is most useful for component connections; there is effectively no
  difference between this and the global level when using a client connection.

* ``node``: (JID assigned, node assigned)

  A handler for this level is responsible for carrying out an action for only one node, and is the
  most specific handler type available. These types of handlers will be most useful for "special"
  nodes that require special processing different than others provided by the JID, such as using
  access control lists, or consolidating data from other nodes.

Default Static Handlers
~~~~~~~~~~~~~~~~~~~~~~~
The XEP-0030 plug-in provides a default set of handlers that work using in-memory
disco stanzas. Each handler simply performs the appropriate lookup or storage
operation using these stanzas without doing any complex operations such as
checking an ACL, etc.

You may find it necessary at some point to revert a particular node or JID to
using the default, static handlers. To do so, use the method ``make_static()``.
You may also elect to only convert a given set of actions instead.

Creating a Node Handler
~~~~~~~~~~~~~~~~~~~~~~~
Every node handler receives three arguments: the JID, the node, and a data
parameter that will contain the relevant information for carrying out the
handler's action, typically a dictionary.

The JID will always have a value, defaulting to ``xmpp.boundjid.full`` for
components or ``xmpp.boundjid.bare`` for clients. The node value may be None or
a string.

Only handlers for the actions ``get_info`` and ``get_items`` need to have return
values. For these actions, DiscoInfo or DiscoItems stanzas are exepected as
output. It is also acceptable for handlers for these actions to generate an
XMPPError exception when necessary.

Example Node Handler:
+++++++++++++++++++++
Here is one of the built-in default handlers as an example:

.. code-block:: python

    def add_identity(self, jid, node, data):
        """
        Add a new identity to the JID/node combination.

        The data parameter may provide:
            category -- The general category to which the agent belongs.
            itype    -- A more specific designation with the category.
            name     -- Optional human readable name for this identity.
            lang     -- Optional standard xml:lang value.
        """
        self.add_node(jid, node)
        self.nodes[(jid, node)]['info'].add_identity(
                data.get('category', ''),
                data.get('itype', ''),
                data.get('name', None),
                data.get('lang', None))

Adding Identities, Features, and Items
--------------------------------------
In order to maintain some backwards compatibility, the methods ``add_identity``,
``add_feature``, and ``add_item`` do not follow the method signature pattern of
the other API methods (i.e. jid, node, then other options), but rather retain
the parameter orders from previous plug-in versions.

Adding an Identity
~~~~~~~~~~~~~~~~~~
Adding an identity may be done using either the older positional notation, or
with keyword parameters. The example below uses the keyword arguments, but in
the same order as expected using positional arguments.

.. code-block:: python

    xmpp['xep_0030'].add_identity(category='client',
                                  itype='bot',
                                  name='Sleek',
                                  node='foo',
                                  jid=xmpp.boundjid.full,
                                  lang='no')

The JID and node values determine which handler will be used to perform the
``add_identity`` action.

The ``lang`` parameter allows for adding localized versions of identities using
the ``xml:lang`` attribute.

Adding a Feature
~~~~~~~~~~~~~~~~
The position ordering for ``add_feature()`` is to include the feature, then
specify the node and then the JID. The JID and node values determine which
handler will be used to perform the ``add_feature`` action.

.. code-block:: python

    xmpp['xep_0030'].add_feature(feature='jabber:x:data',
                                 node='foo',
                                 jid=xmpp.boundjid.full)

Adding an Item
~~~~~~~~~~~~~~
The parameters to ``add_item()`` are potentially confusing due to the fact that
adding an item requires two JID and node combinations: the JID and node of the
item itself, and the JID and node that will own the item.

.. code-block:: python

    xmpp['xep_0030'].add_item(jid='myitemjid@example.com',
                              name='An Item!',
                              node='owner_node',
                              subnode='item_node',
                              ijid=xmpp.boundjid.full)

.. note::

    In this case, the owning JID and node are provided with the
    parameters ``ijid`` and ``node``. 

Performing Disco Queries
-----------------------
The methods ``get_info()`` and ``get_items()`` are used to query remote JIDs
and their nodes for disco information. Since these methods are wrappers for
sending Iq stanzas, they also accept all of the parameters of the ``Iq.send()``
method. The ``get_items()`` method may also accept the boolean parameter
``iterator``, which when set to ``True`` will return an iterator object using
the `XEP-0059 <http://xmpp.org/extensions/xep-0059.html>`_ plug-in.

.. code-block:: python

    info = self['xep_0030'].get_info(jid='foo@example.com',
                                     node='bar',
                                     ifrom='baz@mycomponent.example.com',
                                     block=True,
                                     timeout=30)

    items = self['xep_0030'].get_info(jid='foo@example.com',
                                      node='bar',
                                      iterator=True)

For more examples on how to use basic disco queries, check the ``disco_browser.py``
example in the ``examples`` directory.

Local Queries
~~~~~~~~~~~~~
In some cases, it may be necessary to query the contents of a node owned by the
client itself, or one of a component's many JIDs. The same method is used as for
normal queries, with two differences. First, the parameter ``local=True`` must
be used. Second, the return value will be a DiscoInfo or DiscoItems stanza, not
a full Iq stanza.

.. code-block:: python

    info = self['xep_0030'].get_info(node='foo', local=True)
    items = self['xep_0030'].get_items(jid='somejid@mycomponent.example.com',
                                       node='bar', 
                                       local=True)
