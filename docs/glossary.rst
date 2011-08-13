.. _glossary:

Glossary
========

.. glossary::
    :sorted:

    stream handler
        A callback function that accepts stanza objects pulled directly
        from the XML stream. A stream handler is encapsulated in a
        object that includes a :term:`Matcher` object, and which provides
        additional semantics. For example, the ``Waiter`` handler wrapper
        blocks thread execution until a matching stanza is received.

    event handler
        A callback function that responds to events raised by
        ``XMLStream.event``. An event handler may be marked as
        threaded, allowing it to execute outside of the main processing
        loop.

    stanza object
        Informally may refer both to classes which extend ``ElementBase``
        or ``StanzaBase``, and to objects of such classes.

        A stanza object is a wrapper for an XML object which exposes ``dict``
        like interfaces which may be assigned to, read from, or deleted.

    stanza plugin
        A :term:`stanza object` which has been registered as a potential child
        of another stanza object. The plugin stanza may accessed through the
        parent stanza using the plugin's ``plugin_attrib`` as an interface.

    substanza
        See :term:`stanza plugin`
