from . sleektest import *
from sleekxmpp.xmlstream.stanzabase import ElementBase

class TestElementBase(SleekTest):

    def testExtendedName(self):
        """Test element names of the form tag1/tag2/tag3."""

        class TestStanza(ElementBase):
            name = "foo/bar/baz"
            namespace = "test"

        stanza = TestStanza()
        self.checkStanza(TestStanza, stanza, """
          <foo xmlns="test">
            <bar>
              <baz />
            </bar>
          </foo>
        """)

    def testGetStanzaValues(self):
        """Test getStanzaValues using plugins and substanzas."""

        class TestStanzaPlugin(ElementBase):
            name = "foo2"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))
            plugin_attrib = "foo2"

        class TestSubStanza(ElementBase):
            name = "subfoo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))
            subitem = set((TestSubStanza,))

        registerStanzaPlugin(TestStanza, TestStanzaPlugin)

        stanza = TestStanza()
        stanza['bar'] = 'a'
        stanza['foo2']['baz'] = 'b'
        substanza = TestSubStanza()
        substanza['bar'] = 'c'
        stanza.append(substanza)

        values = stanza.getStanzaValues()
        expected = {'bar': 'a',
                    'baz': '',
                    'foo2': {'bar': '',
                             'baz': 'b'},
                    'substanzas': [{'__childtag__': '{foo}subfoo',
                                    'bar': 'c',
                                    'baz': ''}]}
        self.failUnless(values == expected,
            "Unexpected stanza values:\n%s\n%s" % (str(expected), str(values)))


    def testSetStanzaValues(self):
        """Test using setStanzaValues with substanzas and plugins."""

        class TestStanzaPlugin(ElementBase):
            name = "pluginfoo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))
            plugin_attrib = "plugin_foo"

        class TestStanzaPlugin2(ElementBase):
            name = "pluginfoo2"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))
            plugin_attrib = "plugin_foo2"

        class TestSubStanza(ElementBase):
            name = "subfoo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))
            subitem = set((TestSubStanza,))

        registerStanzaPlugin(TestStanza, TestStanzaPlugin)
        registerStanzaPlugin(TestStanza, TestStanzaPlugin2)

        stanza = TestStanza()
        values = {'bar': 'a',
                  'baz': '',
                  'plugin_foo': {'bar': '',
                                 'baz': 'b'},
                  'plugin_foo2': {'bar': 'd',
                                  'baz': 'e'},
                  'substanzas': [{'__childtag__': '{foo}subfoo',
                                  'bar': 'c',
                                  'baz': ''}]}
        stanza.setStanzaValues(values)

        self.checkStanza(TestStanza, stanza, """
          <foo xmlns="foo" bar="a">
            <pluginfoo baz="b" />
            <pluginfoo2 bar="d" baz="e" />
            <subfoo bar="c" />
          </foo>
        """)

    def testGetItem(self):
        """Test accessing stanza interfaces."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz', 'qux'))
            sub_interfaces = set(('baz',))

            def getQux(self):
              return 'qux'

        class TestStanzaPlugin(ElementBase):
            name = "foobar"
            namespace = "foo"
            plugin_attrib = "foobar"
            interfaces = set(('fizz',))

        TestStanza.subitem = (TestStanza,)
        registerStanzaPlugin(TestStanza, TestStanzaPlugin)

        stanza = TestStanza()
        substanza = TestStanza()
        stanza.append(substanza)
        stanza.setStanzaValues({'bar': 'a',
                                'baz': 'b',
                                'qux': 42,
                                'foobar': {'fizz': 'c'}})

        # Test non-plugin interfaces
        expected = {'substanzas': [substanza],
                    'bar': 'a',
                    'baz': 'b',
                    'qux': 'qux',
                    'meh': ''}
        for interface, value in expected.items():
            result = stanza[interface]
            self.failUnless(result == value,
                "Incorrect stanza interface access result: %s" % result)

        # Test plugin interfaces
        self.failUnless(isinstance(stanza['foobar'], TestStanzaPlugin),
                        "Incorrect plugin object result.")
        self.failUnless(stanza['foobar']['fizz'] == 'c',
                        "Incorrect plugin subvalue result.")

    def testSetItem(self):
        """Test assigning to stanza interfaces."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz', 'qux'))
            sub_interfaces = set(('baz',))

            def setQux(self, value):
                pass

        class TestStanzaPlugin(ElementBase):
            name = "foobar"
            namespace = "foo"
            plugin_attrib = "foobar"
            interfaces = set(('foobar',))

        registerStanzaPlugin(TestStanza, TestStanzaPlugin)

        stanza = TestStanza()

        stanza['bar'] = 'attribute!'
        stanza['baz'] = 'element!'
        stanza['qux'] = 'overridden'
        stanza['foobar'] = 'plugin'

        self.checkStanza(TestStanza, stanza, """
          <foo xmlns="foo" bar="attribute!">
            <baz>element!</baz>
            <foobar foobar="plugin" />
          </foo>
        """)

    def testDelItem(self):
        """Test deleting stanza interface values."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz', 'qux'))
            sub_interfaces = set(('bar',))

            def delQux(self):
                pass

        class TestStanzaPlugin(ElementBase):
            name = "foobar"
            namespace = "foo"
            plugin_attrib = "foobar"
            interfaces = set(('foobar',))

        registerStanzaPlugin(TestStanza, TestStanzaPlugin)

        stanza = TestStanza()
        stanza['bar'] = 'a'
        stanza['baz'] = 'b'
        stanza['qux'] = 'c'
        stanza['foobar']['foobar'] = 'd'

        self.checkStanza(TestStanza, stanza, """
          <foo xmlns="foo" baz="b" qux="c">
            <bar>a</bar>
            <foobar foobar="d" />
          </foo>
        """)

        del stanza['bar']
        del stanza['baz']
        del stanza['qux']
        del stanza['foobar']

        self.checkStanza(TestStanza, stanza, """
          <foo xmlns="foo" qux="c" />
        """)

    def testModifyingAttributes(self):
        """Test modifying top level attributes of a stanza's XML object."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        stanza = TestStanza()

        self.checkStanza(TestStanza, stanza, """
          <foo xmlns="foo" />
        """)

        self.failUnless(stanza._getAttr('bar') == '',
            "Incorrect value returned for an unset XML attribute.")

        stanza._setAttr('bar', 'a')
        stanza._setAttr('baz', 'b')

        self.checkStanza(TestStanza, stanza, """
          <foo xmlns="foo" bar="a" baz="b" />
        """)

        self.failUnless(stanza._getAttr('bar') == 'a',
            "Retrieved XML attribute value is incorrect.")

        stanza._setAttr('bar', None)
        stanza._delAttr('baz')

        self.checkStanza(TestStanza, stanza, """
          <foo xmlns="foo" />
        """)

        self.failUnless(stanza._getAttr('bar', 'c') == 'c',
            "Incorrect default value returned for an unset XML attribute.")
        
    def testGetSubText(self):
        """Test retrieving the contents of a sub element."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar',))

            def setBar(self, value):
                wrapper = ET.Element("{foo}wrapper")
                bar = ET.Element("{foo}bar")
                bar.text = value
                wrapper.append(bar)
                self.xml.append(wrapper)

            def getBar(self):
                return self._getSubText("wrapper/bar", default="not found")

        stanza = TestStanza()
        self.failUnless(stanza['bar'] == 'not found', 
            "Default _getSubText value incorrect.")

        stanza['bar'] = 'found'
        self.checkStanza(TestStanza, stanza, """
          <foo xmlns="foo">
            <wrapper>
              <bar>found</bar>
            </wrapper>
          </foo>
        """)
        self.failUnless(stanza['bar'] == 'found', 
            "_getSubText value incorrect: %s." % stanza['bar'])


suite = unittest.TestLoader().loadTestsFromTestCase(TestElementBase)
