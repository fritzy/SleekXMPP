Send/Receive IQ Stanzas
=======================

Unlike :class:`~sleekxmpp.stanza.message.Message` and
:class:`~sleekxmpp.stanza.presence.Presence` stanzas which only use
text data for basic usage, :class:`~sleekxmpp.stanza.iq.Iq` stanzas
require using XML payloads, and generally entail creating a new
SleekXMPP plugin to provide the necessary convenience methods to
make working with them easier.

Basic Use
---------

XMPP's use of :class:`~sleekxmpp.stanza.iq.Iq` stanzas is built around
namespaced ``<query />`` elements. For clients, just sending the
empty ``<query />`` element will suffice for retrieving information. For
example, a very basic implementation of service discovery would just
need to be able to send:

.. code-block:: xml

    <iq to="user@example.com" type="get" id="1">
      <query xmlns="http://jabber.org/protocol/disco#info" />
    </iq>

Creating Iq Stanzas
~~~~~~~~~~~~~~~~~~~

SleekXMPP provides built-in support for creating basic :class:`~sleekxmpp.stanza.iq.Iq`
stanzas this way. The relevant methods are:

* :meth:`~sleekxmpp.basexmpp.BaseXMPP.make_iq`
* :meth:`~sleekxmpp.basexmpp.BaseXMPP.make_iq_get`
* :meth:`~sleekxmpp.basexmpp.BaseXMPP.make_iq_set`
* :meth:`~sleekxmpp.basexmpp.BaseXMPP.make_iq_result`
* :meth:`~sleekxmpp.basexmpp.BaseXMPP.make_iq_error`
* :meth:`~sleekxmpp.basexmpp.BaseXMPP.make_iq_query`

These methods all follow the same pattern: create or modify an existing 
:class:`~sleekxmpp.stanza.iq.Iq` stanza, set the ``'type'`` value based
on the method name, and finally add a ``<query />`` element with the given
namespace. For example, to produce the query above, you would use:

.. code-block:: python

    self.make_iq_get(queryxmlns='http://jabber.org/protocol/disco#info',
                     ito='user@example.com')


Sending Iq Stanzas
~~~~~~~~~~~~~~~~~~

Once an :class:`~sleekxmpp.stanza.iq.Iq` stanza is created, sending it
over the wire is done using its :meth:`~sleekxmpp.stanza.iq.Iq.send()`
method, like any other stanza object. However, there are a few extra
options to control how to wait for the query's response.

These options are:

* ``block``: The default behaviour is that :meth:`~sleekxmpp.stanza.iq.Iq.send()`
  will block until a response is received and the response stanza will be the
  return value. Setting ``block`` to ``False`` will cause the call to return
  immediately. In which case, you will need to arrange some way to capture
  the response stanza if you need it.

* ``timeout``: When using the blocking behaviour, the call will eventually
  timeout with an error. The default timeout is 30 seconds, but this may
  be overidden two ways. To change the timeout globally, set:

    .. code-block:: python

        self.response_timeout = 10

  To change the timeout for a single call, the ``timeout`` parameter works:

    .. code-block:: python
        
        iq.send(timeout=60)

* ``callback``: When not using a blocking call, using the ``callback``
  argument is a simple way to register a handler that will execute
  whenever a response is finally received. Using this method, there
  is no timeout limit. In case you need to remove the callback, the
  name of the newly created callback is returned.

    .. code-block:: python

       cb_name = iq.send(callback=self.a_callback) 

       # ... later if we need to cancel
       self.remove_handler(cb_name)

Properly working with :class:`~sleekxmpp.stanza.iq.Iq` stanzas requires
handling the intended, normal flow, error responses, and timed out
requests. To make this easier, two exceptions may be thrown by
:meth:`~sleekxmpp.stanza.iq.Iq.send()`: :exc:`~sleekxmpp.exceptions.IqError`
and :exc:`~sleekxmpp.exceptions.IqTimeout`. These exceptions only
apply to the default, blocking calls.

.. code-block:: python

    try:
        resp = iq.send()
        # ... do stuff with expected Iq result
    except IqError as e:
        err_resp = e.iq
        # ... handle error case
    except IqTimeout:
        # ... no response received in time
        pass

If you do not care to distinguish between errors and timeouts, then you
can combine both cases with a generic :exc:`~sleekxmpp.exceptions.XMPPError`
exception:

.. code-block:: python

    try:
        resp = iq.send()
    except XMPPError:
        # ... Don't care about the response
        pass

Advanced Use
------------

Going beyond the basics provided by SleekXMPP requires building at least a
rudimentary SleekXMPP plugin to create a :term:`stanza object` for
interfacting with the :class:`~sleekxmpp.stanza.iq.Iq` payload.

.. seealso::

    * :ref:`create-plugin`
    * :ref:`work-with-stanzas`
    * :ref:`using-handlers-matchers`
    

The typical way to respond to :class:`~sleekxmpp.stanza.iq.Iq` requests is
to register stream handlers. As an example, suppose we create a stanza class
named ``CustomXEP`` which uses the XML element ``<query xmlns="custom-xep" />``,
and has a :attr:`~sleekxmpp.xmlstream.stanzabase.ElementBase.plugin_attrib` value
of ``custom_xep``.

There are two types of incoming :class:`~sleekxmpp.stanza.iq.Iq` requests:
``get`` and ``set``. You can register a handler that will accept both and then
filter by type as needed, as so:

.. code-block:: python

    self.register_handler(Callback(
        'CustomXEP Handler',
        StanzaPath('iq/custom_xep'),
        self._handle_custom_iq))

    # ...

    def _handle_custom_iq(self, iq):
        if iq['type'] == 'get':
            # ...
            pass
        elif iq['type'] == 'set':
            # ...
            pass
        else:
            # ... This will capture error responses too
            pass

If you want to filter out query types beforehand, you can adjust the matching
filter by using ``@type=get`` or ``@type=set`` if you are using the recommended
:class:`~sleekxmpp.xmlstream.matcher.stanzapath.StanzaPath` matcher.

.. code-block:: python

    self.register_handler(Callback(
        'CustomXEP Handler',
        StanzaPath('iq@type=get/custom_xep'),
        self._handle_custom_iq_get))

    # ...

    def _handle_custom_iq_get(self, iq):
        assert(iq['type'] == 'get')
