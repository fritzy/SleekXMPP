from sleekxmpp.xmlstream import ElementBase

class Action(ElementBase):

    """
    A stanza class for XML content of the form:

    <action xmlns="sleekxmpp:custom:actions">
      <method>X</method>
      <param>X</param>
      <status>X</status>
    </action>
    """
   
    #: The `name` field refers to the basic XML tag name of the
    #: stanza. Here, the tag name will be 'action'.
    name = 'action'

    #: The namespace of the main XML tag.
    namespace = 'sleekxmpp:custom:actions'

    #: The `plugin_attrib` value is the name that can be used
    #: with a parent stanza to access this stanza. For example
    #: from an Iq stanza object, accessing:
    #: 
    #:     iq['action']
    #: 
    #: would reference an Action object, and will even create
    #: an Action object and append it to the Iq stanza if
    #: one doesn't already exist.
    plugin_attrib = 'action'

    #: Stanza objects expose dictionary-like interfaces for
    #: accessing and manipulating substanzas and other values.
    #: The set of interfaces defined here are the names of
    #: these dictionary-like interfaces provided by this stanza
    #: type. For example, an Action stanza object can use:
    #:
    #:     action['method'] = 'foo'
    #:     print(action['param'])
    #:     del action['status']
    #:
    #: to set, get, or remove its values.
    interfaces = set(('method', 'param', 'status'))

    #: By default, values in the `interfaces` set are mapped to
    #: attribute values. This can be changed such that an interface
    #: maps to a subelement's text value by adding interfaces to
    #: the sub_interfaces set. For example, here all interfaces
    #: are marked as sub_interfaces, and so the XML produced will
    #: look like:
    #: 
    #:     <action xmlns="sleekxmpp:custom:actions">
    #:       <method>foo</method>
    #:     </action>
    sub_interfaces = interfaces
