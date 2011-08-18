SleekXMPP
#########

SleekXMPP is an MIT licensed XMPP library for Python 2.6/3.1+,
and is featured in examples in
`XMPP: The Definitive Guide <http://oreilly.com/catalog/9780596521271>`_ 
by Kevin Smith, Remko Tronçon, and Peter Saint-Andre. If you've arrived
here from reading the Definitive Guide, please see the notes on updating
the examples to the latest version of SleekXMPP.

SleekXMPP's design goals and philosphy are:

**Low number of dependencies**
    Installing and using SleekXMPP should be as simple as possible, without
    having to deal with long dependency chains.

    As part of reducing the number of dependencies, some third party
    modules are included with SleekXMPP in the ``thirdparty`` directory.
    Imports from this module first try to import an existing installed
    version before loading the packaged version, when possible.

**Every XEP as a plugin**
    Following Python's "batteries included" approach, the goal is to
    provide support for all currently active XEPs (final and draft). Since
    adding XEP support is done through easy to create plugins, the hope is
    to also provide a solid base for implementing and creating experimental
    XEPs.

**Rewarding to work with**
    As much as possible, SleekXMPP should allow things to "just work" using
    sensible defaults and appropriate abstractions. XML can be ugly to work
    with, but it doesn't have to be that way.


Get the Code
------------
.. code-block:: sh

    pip install sleekxmpp

The latest source code for SleekXMPP may be found on `Github
<http://github.com/fritzy/SleekXMPP>`_. Releases can be found in the
``master`` branch, while the latest development version is in the
``develop`` branch.

**Stable Releases**
    - `1.0 Beta6.1 <http://github.com/fritzy/SleekXMPP/zipball/1.0-Beta6.1>`_  
    - `1.0 Beta5 <http://github.com/fritzy/SleekXMPP/zipball/1.0-Beta5>`_
    - `1.0 Beta4 <http://github.com/fritzy/SleekXMPP/zipball/1.0-Beta4>`_
    - `1.0 Beta3 <http://github.com/fritzy/SleekXMPP/zipball/1.0-Beta3>`_
    - `1.0 Beta2 <http://github.com/fritzy/SleekXMPP/zipball/1.0-Beta2>`_
    - `1.0 Beta1 <http://github.com/fritzy/SleekXMPP/zipball/1.0-Beta1>`_

**Develop Releases**
    - `Latest Develop Version <http://github.com/fritzy/SleekXMPP/zipball/develop>`_


Discussion
----------
A mailing list and XMPP chat room are available for discussing and getting
help with SleekXMPP.

**Mailing List**
    `SleekXMPP Discussion on Google Groups <http://groups.google.com/group/sleekxmpp-discussion>`_

**Chat**
    `sleek@conference.jabber.org <xmpp:sleek@conference.jabber.org?join>`_


Credits
-------
**Main Author:** Nathan Fritz
    `fritzy@netflint.net <xmpp:fritzy@netflint.net?message>`_, 
    `@fritzy <http://twitter.com/fritzy>`_

    Nathan is also the author of XMPPHP and `Seesmic-AS3-XMPP
    <http://code.google.com/p/seesmic-as3-xmpp/>`_, and a member of the XMPP
    Council.

**Co-Author:** Lance Stout
    `lancestout@gmail.com <xmpp:lancestout@gmail.com?message>`_, 
    `@lancestout <http://twitter.com/lancestout>`_

**Contributors:**
    - Brian Beggs (`macdiesel <http://github.com/macdiesel>`_)
    - Dann Martens (`dannmartens <http://github.com/dannmartens>`_)
    - Florent Le Coz (`louiz <http://github.com/louiz>`_)
    - Kevin Smith (`Kev <http://github.com/Kev>`_, http://kismith.co.uk)
    - Remko Tronçon (`remko <http://github.com/remko>`_, http://el-tramo.be)
    - Te-jé Rogers (`te-je <http://github.com/te-je>`_)
    - Thom Nichols (`tomstrummer <http://github.com/tomstrummer>`_)
