.. _create-plugin:

Creating a SleekXMPP Plugin
===========================

One of the goals of SleekXMPP is to provide support for every draft or final
XMPP extension (`XEP <http://xmpp.org/extensions/>`_). To do this, SleekXMPP has a
plugin mechanism for adding the functionalities required by each XEP. But even
though plugins were made to quickly implement and prototype the official XMPP
extensions, there is no reason you can't create your own plugin to implement
your own custom XMPP-based protocol.

This guide will help walk you through the steps to
implement a rudimentary version of `XEP-0077 In-band
Registration <http://xmpp.org/extensions/xep-0077.html>`_. In-band registration
was implemented in example 14-6 (page 223) of `XMPP: The Definitive
Guide <http://oreilly.com/catalog/9780596521271>`_ because there was no SleekXMPP
plugin for XEP-0077 at the time of writing. We will partially fix that issue
here by turning the example implementation from *XMPP: The Definitive Guide*
into a plugin. Again, note that this will not a complete implementation, and a
different, more robust, official plugin for XEP-0077 may be added to SleekXMPP
in the future.

.. note::

    The example plugin created in this guide is for the server side of the
    registration process only. It will **NOT** be able to register new accounts
    on an XMPP server.

First Steps
-----------
Every plugin inherits from the class :mod:`base_plugin <sleekxmpp.plugins.base.base_plugin>`,
and must include a ``plugin_init`` method. While the
plugins distributed with SleekXMPP must be placed in the plugins directory
``sleekxmpp/plugins`` to be loaded, custom plugins may be loaded from any
module. To do so, use the following form when registering the plugin:

.. code-block:: python

    self.register_plugin('myplugin', module=mod_containing_my_plugin)

The plugin name must be the same as the plugin's class name.
 
Now, we can open our favorite text editors and create ``xep_0077.py`` in
``SleekXMPP/sleekxmpp/plugins``. We want to do some basic house-keeping and
declare the name and description of the XEP we are implementing. If you
are creating your own custom plugin, you don't need to include the ``xep``
attribute.

.. code-block:: python

    """
    Creating a SleekXMPP Plugin

    This is a minimal implementation of XEP-0077 to serve
    as a tutorial for creating SleekXMPP plugins.
    """

    from sleekxmpp.plugins.base import base_plugin

    class xep_0077(base_plugin):
        """
        XEP-0077 In-Band Registration
        """

        def plugin_init(self):
            self.description = "In-Band Registration"
            self.xep = "0077"

Now that we have a basic plugin, we need to edit
``sleekxmpp/plugins/__init__.py`` to include our new plugin by adding
``'xep_0077'`` to the ``__all__`` declaration.

Interacting with Other Plugins
------------------------------

In-band registration is a feature that should be advertised through `Service
Discovery <http://xmpp.org/extensions/xep-0030.html>`_. To do that, we tell the
``xep_0030`` plugin to add the ``"jabber:iq:register"`` feature. We put this
call in a method named ``post_init`` which will be called once the plugin has
been loaded; by doing so we advertise that we can do registrations only after we
finish activating the plugin.

The ``post_init`` method needs to call ``base_plugin.post_init(self)``
which will mark that ``post_init`` has been called for the plugin. Once the
SleekXMPP object begins processing, ``post_init`` will be called on any plugins
that have not already run ``post_init``. This allows you to register plugins and
their dependencies without needing to worry about the order in which you do so.

**Note:** by adding this call we have introduced a dependency on the XEP-0030
plugin. Be sure to register ``'xep_0030'`` as well as ``'xep_0077'``. SleekXMPP
does not automatically load plugin dependencies for you.

.. code-block:: python

    def post_init(self):
        base_plugin.post_init(self)
        self.xmpp['xep_0030'].add_feature("jabber:iq:register")

Creating Custom Stanza Objects
------------------------------

Now, the IQ stanzas needed to implement our version of XEP-0077 are not very
complex, and we could just interact with the XML objects directly just like
in the *XMPP: The Definitive Guide* example. However, creating custom stanza
objects is good practice.

We will create a new ``Registration`` stanza. Following the *XMPP: The
Definitive Guide* example, we will add support for a username and password
field. We also need two flags: ``registered`` and ``remove``. The ``registered``
flag is sent when an already registered user attempts to register, along with
their registration data. The ``remove`` flag is a request to unregister a user's
account.

Adding additional `fields specified in
XEP-0077 <http://xmpp.org/extensions/xep-0077.html#registrar-formtypes-register>`_
will not be difficult and is left as an exercise for the reader.

Our ``Registration`` class needs to start with a few descriptions of its
behaviour:

* ``namespace``
    The namespace our stanza object lives in. In this case,
    ``"jabber:iq:register"``.

* ``name``
    The name of the root XML element. In this case, the ``query`` element.

* ``plugin_attrib``
    The name to access this type of stanza. In particular, given a
    registration stanza, the ``Registration`` object can be found using:
    ``iq_object['register']``.

* ``interfaces``
    A list of dictionary-like keys that can be used with the stanza object.
    When using ``"key"``, if there exists a method of the form ``getKey``,
    ``setKey``, or``delKey`` (depending on context) then the result of calling
    that method will be returned. Otherwise, the value of the attribute ``key``
    of the main stanza element is returned if one exists.

    **Note:** The accessor methods currently use title case, and not camel case.
    Thus if you need to access an item named ``"methodName"`` you will need to
    use ``getMethodname``. This naming convention might change to full camel
    case in a future version of SleekXMPP.

* ``sub_interfaces``
    A subset of ``interfaces``, but these keys map to the text of any
    subelements that are direct children of the main stanza element. Thus,
    referencing ``iq_object['register']['username']`` will either execute
    ``getUsername`` or return the value in the ``username`` element of the
    query.

    If you need to access an element, say ``elem``, that is not a direct child
    of the main stanza element, you will need to add ``getElem``, ``setElem``,
    and ``delElem``. See the note above about naming conventions.

.. code-block:: python

    from sleekxmpp.xmlstream import ElementBase, ET, JID, register_stanza_plugin
    from sleekxmpp import Iq

    class Registration(ElementBase):
        namespace = 'jabber:iq:register'
        name = 'query'
        plugin_attrib = 'register'
        interfaces = set(('username', 'password', 'registered', 'remove'))
        sub_interfaces = interfaces

        def getRegistered(self):
            present = self.xml.find('{%s}registered' % self.namespace)
            return present is not None

        def getRemove(self):
            present = self.xml.find('{%s}remove' % self.namespace)
            return present is not None

        def setRegistered(self, registered):
            if registered:
                self.addField('registered')
            else:
                del self['registered']

        def setRemove(self, remove):
            if remove:
                self.addField('remove')
            else:
                del self['remove']

        def addField(self, name):
            itemXML = ET.Element('{%s}%s' % (self.namespace, name))
            self.xml.append(itemXML)

Setting a ``sub_interface`` attribute to ``""`` will remove that subelement.
Since we want to include empty registration fields in our form, we need the
``addField`` method to add the empty elements.

Since the ``registered`` and ``remove`` elements are just flags, we need to add
custom logic to enforce the binary behavior.

Extracting Stanzas from the XML Stream
--------------------------------------

Now that we have a custom stanza object, we need to be able to detect when we
receive one. To do this, we register a stream handler that will pattern match
stanzas off of the XML stream against our stanza object's element name and
namespace. To do so, we need to create a ``Callback`` object which contains
an XML fragment that can identify our stanza type. We can add this handler
registration to our ``plugin_init`` method.

Also, we need to associate our ``Registration`` class with IQ stanzas;
that requires the use of the ``register_stanza_plugin`` function (in
``sleekxmpp.xmlstream.stanzabase``) which takes the class of a parent stanza
type followed by the substanza type. In our case, the parent stanza is an IQ
stanza, and the substanza is our registration query.

The ``__handleRegistration`` method referenced in the callback will be our
handler function to process registration requests.

.. code-block:: python

    def plugin_init(self):
        self.description = "In-Band Registration"
        self.xep = "0077"

        self.xmpp.register_handler(
          Callback('In-Band Registration',
            MatchXPath('{%s}iq/{jabber:iq:register}query' % self.xmpp.default_ns),
            self.__handleRegistration))
        register_stanza_plugin(Iq, Registration)

Handling Incoming Stanzas and Triggering Events
-----------------------------------------------
There are six situations that we need to handle to finish our implementation of
XEP-0077.

**Registration Form Request from a New User:**

    .. code-block:: xml

        <iq type="result">
         <query xmlns="jabber:iq:register">
          <username />
          <password />
         </query>
        </iq>

**Registration Form Request from an Existing User:**

    .. code-block:: xml

        <iq type="result">
         <query xmlns="jabber:iq:register">
          <registered />
          <username>Foo</username>
          <password>hunter2</password>
         </query>
        </iq>

**Unregister Account:**

    .. code-block:: xml

        <iq type="result">
         <query xmlns="jabber:iq:register" />
        </iq>

**Incomplete Registration:**

    .. code-block:: xml

        <iq type="error">
          <query xmlns="jabber:iq:register">
            <username>Foo</username>
          </query>
         <error code="406" type="modify">
          <not-acceptable xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
         </error>
        </iq>

**Conflicting Registrations:**

    .. code-block:: xml

        <iq type="error">
         <query xmlns="jabber:iq:register">
          <username>Foo</username>
          <password>hunter2</password>
         </query>
         <error code="409" type="cancel">
          <conflict xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />
         </error>
        </iq>

**Successful Registration:**

    .. code-block:: xml

        <iq type="result">
         <query xmlns="jabber:iq:register" />
        </iq>

Cases 1 and 2: Registration Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Responding to registration requests depends on if the requesting user already
has an account. If there is an account, the response should include the
``registered`` flag and the user's current registration information. Otherwise,
we just send the fields for our registration form.

We will handle both cases by creating a ``sendRegistrationForm`` method that
will create either an empty of full form depending on if we provide it with
user data. Since we need to know which form fields to include (especially if we
add support for the other fields specified in XEP-0077), we will also create a
method ``setForm`` which will take the names of the fields we wish to include.

.. code-block:: python

    def plugin_init(self):
        self.description = "In-Band Registration"
        self.xep = "0077"
        self.form_fields = ('username', 'password')
        ... remainder of plugin_init

    ...

    def __handleRegistration(self, iq):
        if iq['type'] == 'get':
            # Registration form requested
            userData = self.backend[iq['from'].bare]
            self.sendRegistrationForm(iq, userData)

    def setForm(self, *fields):
        self.form_fields = fields

    def sendRegistrationForm(self, iq, userData=None):
        reg = iq['register']
        if userData is None:
            userData = {}
        else:
            reg['registered'] = True

        for field in self.form_fields:
            data = userData.get(field, '')
            if data:
                # Add field with existing data
                reg[field] = data
            else:
                # Add a blank field
                reg.addField(field)

        iq.reply().setPayload(reg.xml)
        iq.send()

Note how we are able to access our ``Registration`` stanza object with
``iq['register']``.

A User Backend
++++++++++++++
You might have noticed the reference to ``self.backend``, which is an object
that abstracts away storing and retrieving user information. Since it is not
much more than a dictionary, we will leave the implementation details to the
final, full source code example.

Case 3: Unregister an Account
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The next simplest case to consider is responding to a request to remove
an account. If we receive a ``remove`` flag, we instruct the backend to
remove the user's account. Since your application may need to know about
when users are registered or unregistered, we trigger an event using
``self.xmpp.event('unregister_user', iq)``. See the component examples below for
how to respond to that event.

.. code-block:: python

     def __handleRegistration(self, iq):
        if iq['type'] == 'get':
            # Registration form requested
            userData = self.backend[iq['from'].bare]
            self.sendRegistrationForm(iq, userData)
        elif iq['type'] == 'set':
            # Remove an account
            if iq['register']['remove']:
                self.backend.unregister(iq['from'].bare)
                self.xmpp.event('unregistered_user', iq)
                iq.reply().send()
                return

Case 4: Incomplete Registration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For the next case we need to check the user's registration to ensure it has all
of the fields we wanted. The simple option that we will use is to loop over the
field names and check each one; however, this means that all fields we send to
the user are required. Adding optional fields is left to the reader.

Since we have received an incomplete form, we need to send an error message back
to the user. We have to send a few different types of errors, so we will also
create a ``_sendError`` method that will add the appropriate ``error`` element
to the IQ reply.

.. code-block:: python

    def __handleRegistration(self, iq):
        if iq['type'] == 'get':
            # Registration form requested
            userData = self.backend[iq['from'].bare]
            self.sendRegistrationForm(iq, userData)
        elif iq['type'] == 'set':
            if iq['register']['remove']:
                # Remove an account
                self.backend.unregister(iq['from'].bare)
                self.xmpp.event('unregistered_user', iq)
                iq.reply().send()
                return

            for field in self.form_fields:
                if not iq['register'][field]:
                    # Incomplete Registration
                    self._sendError(iq, '406', 'modify', 'not-acceptable'
                                    "Please fill in all fields.")
                    return

    ...

    def _sendError(self, iq, code, error_type, name, text=''):
        iq.reply().setPayload(iq['register'].xml)
        iq.error()
        iq['error']['code'] = code
        iq['error']['type'] = error_type
        iq['error']['condition'] = name
        iq['error']['text'] = text
        iq.send()

Cases 5 and 6: Conflicting and Successful Registration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
We are down to the final decision on if we have a successful registration. We
send the user's data to the backend with the ``self.backend.register`` method.
If it returns ``True``, then registration has been successful. Otherwise,
there has been a conflict with usernames and registration has failed. Like
with unregistering an account, we trigger an event indicating that a user has
been registered by using ``self.xmpp.event('registered_user', iq)``. See the
component examples below for how to respond to this event.

.. code-block:: python

    def __handleRegistration(self, iq):
        if iq['type'] == 'get':
            # Registration form requested
            userData = self.backend[iq['from'].bare]
            self.sendRegistrationForm(iq, userData)
        elif iq['type'] == 'set':
            if iq['register']['remove']:
                # Remove an account
                self.backend.unregister(iq['from'].bare)
                self.xmpp.event('unregistered_user', iq)
                iq.reply().send()
                return

            for field in self.form_fields:
                if not iq['register'][field]:
                    # Incomplete Registration
                    self._sendError(iq, '406', 'modify', 'not-acceptable',
                                    "Please fill in all fields.")
                    return

            if self.backend.register(iq['from'].bare, iq['register']):
                # Successful registration
                self.xmpp.event('registered_user', iq)
                iq.reply().setPayload(iq['register'].xml)
                iq.send()
            else:
                # Conflicting registration
                self._sendError(iq, '409', 'cancel', 'conflict',
                                "That username is already taken.")

Example Component Using the XEP-0077 Plugin
-------------------------------------------
Alright, the moment we've been working towards - actually using our plugin to
simplify our other applications. Here is a basic component that simply manages
user registrations and sends the user a welcoming message when they register,
and a farewell message when they delete their account.

Note that we have to register the ``'xep_0030'`` plugin first,
and that we specified the form fields we wish to use with
``self.xmpp.plugin['xep_0077'].setForm('username', 'password')``.

.. code-block:: python

    import sleekxmpp.componentxmpp

    class Example(sleekxmpp.componentxmpp.ComponentXMPP):

        def __init__(self, jid, password):
            sleekxmpp.componentxmpp.ComponentXMPP.__init__(self, jid, password, 'localhost', 8888)

            self.registerPlugin('xep_0030')
            self.registerPlugin('xep_0077')
            self.plugin['xep_0077'].setForm('username', 'password')

            self.add_event_handler("registered_user", self.reg)
            self.add_event_handler("unregistered_user", self.unreg)

        def reg(self, iq):
            msg = "Welcome! %s" % iq['register']['username']
            self.sendMessage(iq['from'], msg, mfrom=self.fulljid)

        def unreg(self, iq):
            msg = "Bye! %s" % iq['register']['username']
            self.sendMessage(iq['from'], msg, mfrom=self.fulljid)

**Congratulations!** We now have a basic, functioning implementation of
XEP-0077.

Complete Source Code for XEP-0077 Plugin
----------------------------------------
Here is a copy of a more complete implementation of the plugin we created, but
with some additional registration fields implemented.

.. code-block:: python

    """
    Creating a SleekXMPP Plugin

    This is a minimal implementation of XEP-0077 to serve
    as a tutorial for creating SleekXMPP plugins.
    """

    from sleekxmpp.plugins.base import base_plugin
    from sleekxmpp.xmlstream.handler.callback import Callback
    from sleekxmpp.xmlstream.matcher.xpath import MatchXPath
    from sleekxmpp.xmlstream import ElementBase, ET, JID, register_stanza_plugin
    from sleekxmpp import Iq
    import copy


    class Registration(ElementBase):
        namespace = 'jabber:iq:register'
        name = 'query'
        plugin_attrib = 'register'
        interfaces = set(('username', 'password', 'email', 'nick', 'name', 
                          'first', 'last', 'address', 'city', 'state', 'zip', 
                          'phone', 'url', 'date', 'misc', 'text', 'key', 
                          'registered', 'remove', 'instructions'))
        sub_interfaces = interfaces

        def getRegistered(self):
            present = self.xml.find('{%s}registered' % self.namespace)
            return present is not None

        def getRemove(self):
            present = self.xml.find('{%s}remove' % self.namespace)
            return present is not None

        def setRegistered(self, registered):
            if registered:
                self.addField('registered')
            else:
                del self['registered']

        def setRemove(self, remove):
            if remove:
                self.addField('remove')
            else:
                del self['remove']

        def addField(self, name):
            itemXML = ET.Element('{%s}%s' % (self.namespace, name))
            self.xml.append(itemXML)


    class UserStore(object):
        def __init__(self):
            self.users = {}

        def __getitem__(self, jid):
            return self.users.get(jid, None)

        def register(self, jid, registration):
            username = registration['username']

            def filter_usernames(user):
                return user != jid and self.users[user]['username'] == username

            conflicts = filter(filter_usernames, self.users.keys())
            if conflicts:
                return False

            self.users[jid] = registration
            return True

        def unregister(self, jid):
            del self.users[jid]

    class xep_0077(base_plugin):
        """
        XEP-0077 In-Band Registration
        """

        def plugin_init(self):
            self.description = "In-Band Registration"
            self.xep = "0077"
            self.form_fields = ('username', 'password')
            self.form_instructions = ""
            self.backend = UserStore()

            self.xmpp.register_handler(
                Callback('In-Band Registration',
                         MatchXPath('{%s}iq/{jabber:iq:register}query' % self.xmpp.default_ns),
                         self.__handleRegistration))
            register_stanza_plugin(Iq, Registration)

        def post_init(self):
            base_plugin.post_init(self)
            self.xmpp['xep_0030'].add_feature("jabber:iq:register")

        def __handleRegistration(self, iq):
            if iq['type'] == 'get':
                # Registration form requested
                userData = self.backend[iq['from'].bare]
                self.sendRegistrationForm(iq, userData)
            elif iq['type'] == 'set':
                if iq['register']['remove']:
                    # Remove an account
                    self.backend.unregister(iq['from'].bare)
                    self.xmpp.event('unregistered_user', iq)
                    iq.reply().send()
                    return

                for field in self.form_fields:
                    if not iq['register'][field]:
                        # Incomplete Registration
                        self._sendError(iq, '406', 'modify', 'not-acceptable',
                                        "Please fill in all fields.")
                        return

                if self.backend.register(iq['from'].bare, iq['register']):
                    # Successful registration
                    self.xmpp.event('registered_user', iq)
                    iq.reply().setPayload(iq['register'].xml)
                    iq.send()
                else:
                    # Conflicting registration
                    self._sendError(iq, '409', 'cancel', 'conflict',
                                    "That username is already taken.")

        def setForm(self, *fields):
            self.form_fields = fields

        def setInstructions(self, instructions):
            self.form_instructions = instructions

        def sendRegistrationForm(self, iq, userData=None):
            reg = iq['register']
            if userData is None:
                userData = {}
            else:
                reg['registered'] = True

            if self.form_instructions:
                reg['instructions'] = self.form_instructions

            for field in self.form_fields:
                data = userData.get(field, '')
                if data:
                    # Add field with existing data
                    reg[field] = data
                else:
                    # Add a blank field
                    reg.addField(field)

            iq.reply().setPayload(reg.xml)
            iq.send()

        def _sendError(self, iq, code, error_type, name, text=''):
            iq.reply().setPayload(iq['register'].xml)
            iq.error()
            iq['error']['code'] = code
            iq['error']['type'] = error_type
            iq['error']['condition'] = name
            iq['error']['text'] = text
            iq.send()
