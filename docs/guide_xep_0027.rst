XEP-0027: Working with OpenPGP messaging and presence
=====================================================

The XEP-0027 extension enables signing of presence and the encryption of
messages using respective OpenPGP operations.

Prerequisites
-------------
The XEP-0027 plugin uses GnuPG, accessed through `python-gnupg module
<https://pythonhosted.org/python-gnupg/>`_, hence you need to have GnuPG
installed (the python module is included in sleekxmpp). Also, you need to
generate your keys externally and make the plugin aware of it by calling

.. code-block:: python

    self.plugin['xep_0027'].set_keyid(jid=jid, keyid=keyid)

with ``keyid`` being any accepted by the gpg program (such as fingerprint or
any part of the name/E-Mail and ``jid`` being the one associated with the key,
set to ``None`` for yourself.

Signing your presence
---------------------
Activating the plugin by

.. code-block:: python

    xmpp.register_plugin('xep_0027')

(whereas ``xmpp`` is your ``ClientXMPP`` object) automatically signs your
presence when calling ``self.send_presence()``. It will add the signature into
a ``x xmlns="jabber:x:signed"`` stanza.

Encrypting/decrypting messages
------------------------------
The standard defines the ``x xmlns='jabber:x:encrypted'`` stanza for messages
that contains the encrypted message, whilst the ``body`` of such message would
only contain a note about the encryption. The routine of sending an encrypted
message would be thus like (within ``ClientXMPP``)

.. code-block:: python
 
    msg = self.make_message(mto='recipient@dukgo.com',
                            mbody='Please use XEP-0027',
                            mtype='chat')
    msg['encrypted'] = 'Here is my actual message!'
    msg.send()

The decrypted contents of a received message can be obtained by just calling
``msg['encrypted']``.
