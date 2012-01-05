.. _proxy:

=========================
Enable HTTP Proxy Support
=========================

.. note::
    
    If you have any issues working through this quickstart guide
    or the other tutorials here, please either send a message to the
    `mailing list <http://groups.google.com/group/sleekxmpp-discussion>`_
    or join the chat room at `sleek@conference.jabber.org
    <xmpp:sleek@conference.jabber.org?join>`_.

In some instances, you may wish to route XMPP traffic through
an HTTP proxy, probably to get around restrictive firewalls.
SleekXMPP provides support for basic HTTP proxying with DIGEST
authentication.

Enabling proxy support is done in two steps. The first is to instruct SleekXMPP
to use a proxy, and the second is to configure the proxy details:

.. code-block:: python

    xmpp = ClientXMPP(...)
    xmpp.use_proxy = True
    xmpp.proxy_config = {
        'host': 'proxy.example.com',
        'port': 5555,
        'username': 'example_user',
        'password': '******'
    }

The ``'username'`` and ``'password'`` fields are optional if the proxy does not
require authentication.


The Final Product
-----------------

.. include:: ../../examples/proxy_echo_client.py
    :literal:
