import unittest
from sleekxmpp.test import SleekTest
from sleekxmpp.xmlstream.stanzabase import ElementBase, register_stanza_plugin, ET
from sleekxmpp.thirdparty import OrderedDict


class TestElementBase(SleekTest):

    def testFixNs(self):
        """Test fixing namespaces in an XPath expression."""

        e = ElementBase()
        ns = "http://jabber.org/protocol/disco#items"
        result = e._fix_ns("{%s}foo/bar/{abc}baz/{%s}more" % (ns, ns))

        expected = "/".join(["{%s}foo" % ns,
                             "{%s}bar" % ns,
                             "{abc}baz",
                             "{%s}more" % ns])
        self.failUnless(expected == result,
            "Incorrect namespace fixing result: %s" % str(result))


    def testExtendedName(self):
        """Test element names of the form tag1/tag2/tag3."""

        class TestStanza(ElementBase):
            name = "foo/bar/baz"
            namespace = "test"

        stanza = TestStanza()
        self.check(stanza, """
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

        register_stanza_plugin(TestStanza, TestStanzaPlugin, iterable=True)

        stanza = TestStanza()
        stanza['bar'] = 'a'
        stanza['foo2']['baz'] = 'b'
        substanza = TestSubStanza()
        substanza['bar'] = 'c'
        stanza.append(substanza)

        values = stanza.getStanzaValues()
        expected = {'lang': '',
                    'bar': 'a',
                    'baz': '',
                    'foo2': {'lang': '',
                             'bar': '',
                             'baz': 'b'},
                    'substanzas': [{'__childtag__': '{foo}foo2',
                                    'lang': '',
                                    'bar': '',
                                    'baz': 'b'},
                                   {'__childtag__': '{foo}subfoo',
                                    'lang': '',
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

        register_stanza_plugin(TestStanza, TestSubStanza, iterable=True)
        register_stanza_plugin(TestStanza, TestStanzaPlugin)
        register_stanza_plugin(TestStanza, TestStanzaPlugin2)

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
        stanza.values = values

        self.check(stanza, """
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

        register_stanza_plugin(TestStanza, TestStanza, iterable=True)
        register_stanza_plugin(TestStanza, TestStanzaPlugin)

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

        register_stanza_plugin(TestStanza, TestStanzaPlugin)

        stanza = TestStanza()

        stanza['bar'] = 'attribute!'
        stanza['baz'] = 'element!'
        stanza['qux'] = 'overridden'
        stanza['foobar'] = 'plugin'

        self.check(stanza, """
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

        register_stanza_plugin(TestStanza, TestStanzaPlugin)

        stanza = TestStanza()
        stanza['bar'] = 'a'
        stanza['baz'] = 'b'
        stanza['qux'] = 'c'
        stanza['foobar']['foobar'] = 'd'

        self.check(stanza, """
          <foo xmlns="foo" baz="b" qux="c">
            <bar>a</bar>
            <foobar foobar="d" />
          </foo>
        """)

        del stanza['bar']
        del stanza['baz']
        del stanza['qux']
        del stanza['foobar']

        self.check(stanza, """
          <foo xmlns="foo" qux="c" />
        """)

    def testModifyingAttributes(self):
        """Test modifying top level attributes of a stanza's XML object."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        stanza = TestStanza()

        self.check(stanza, """
          <foo xmlns="foo" />
        """)

        self.failUnless(stanza._get_attr('bar') == '',
            "Incorrect value returned for an unset XML attribute.")

        stanza._set_attr('bar', 'a')
        stanza._set_attr('baz', 'b')

        self.check(stanza, """
          <foo xmlns="foo" bar="a" baz="b" />
        """)

        self.failUnless(stanza._get_attr('bar') == 'a',
            "Retrieved XML attribute value is incorrect.")

        stanza._set_attr('bar', None)
        stanza._del_attr('baz')

        self.check(stanza, """
          <foo xmlns="foo" />
        """)

        self.failUnless(stanza._get_attr('bar', 'c') == 'c',
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
                return self._get_sub_text("wrapper/bar", default="not found")

        stanza = TestStanza()
        self.failUnless(stanza['bar'] == 'not found',
            "Default _get_sub_text value incorrect.")

        stanza['bar'] = 'found'
        self.check(stanza, """
          <foo xmlns="foo">
            <wrapper>
              <bar>found</bar>
            </wrapper>
          </foo>
        """)
        self.failUnless(stanza['bar'] == 'found',
            "_get_sub_text value incorrect: %s." % stanza['bar'])

    def testSubElement(self):
        """Test setting the contents of a sub element."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

            def setBaz(self, value):
                self._set_sub_text("wrapper/baz", text=value)

            def getBaz(self):
                return self._get_sub_text("wrapper/baz")

            def setBar(self, value):
                self._set_sub_text("wrapper/bar", text=value)

            def getBar(self):
                return self._get_sub_text("wrapper/bar")

        stanza = TestStanza()
        stanza['bar'] = 'a'
        stanza['baz'] = 'b'
        self.check(stanza, """
          <foo xmlns="foo">
            <wrapper>
              <bar>a</bar>
              <baz>b</baz>
            </wrapper>
          </foo>
        """)
        stanza._set_sub_text('wrapper/bar', text='', keep=True)
        self.check(stanza, """
          <foo xmlns="foo">
            <wrapper>
              <bar />
              <baz>b</baz>
            </wrapper>
          </foo>
        """, use_values=False)

        stanza['bar'] = 'a'
        stanza._set_sub_text('wrapper/bar', text='')
        self.check(stanza, """
          <foo xmlns="foo">
            <wrapper>
              <baz>b</baz>
            </wrapper>
          </foo>
        """)

    def testDelSub(self):
        """Test removing sub elements."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

            def setBar(self, value):
                self._set_sub_text("path/to/only/bar", value)

            def getBar(self):
                return self._get_sub_text("path/to/only/bar")

            def delBar(self):
                self._del_sub("path/to/only/bar")

            def setBaz(self, value):
                self._set_sub_text("path/to/just/baz", value)

            def getBaz(self):
                return self._get_sub_text("path/to/just/baz")

            def delBaz(self):
                self._del_sub("path/to/just/baz")

        stanza = TestStanza()
        stanza['bar'] = 'a'
        stanza['baz'] = 'b'

        self.check(stanza, """
          <foo xmlns="foo">
            <path>
              <to>
                <only>
                  <bar>a</bar>
                </only>
                <just>
                  <baz>b</baz>
                </just>
              </to>
            </path>
          </foo>
        """)

        del stanza['bar']
        del stanza['baz']

        self.check(stanza, """
          <foo xmlns="foo">
            <path>
              <to>
                <only />
                <just />
              </to>
            </path>
          </foo>
        """, use_values=False)

        stanza['bar'] = 'a'
        stanza['baz'] = 'b'

        stanza._del_sub('path/to/only/bar', all=True)

        self.check(stanza, """
          <foo xmlns="foo">
            <path>
              <to>
                <just>
                  <baz>b</baz>
                </just>
              </to>
            </path>
          </foo>
        """)

    def testMatch(self):
        """Test matching a stanza against an XPath expression."""

        class TestSubStanza(ElementBase):
            name = "sub"
            namespace = "baz"
            interfaces = set(('attrib',))

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar','baz', 'qux'))
            sub_interfaces = set(('qux',))

            def setQux(self, value):
                self._set_sub_text('qux', text=value)

            def getQux(self):
                return self._get_sub_text('qux')

        class TestStanzaPlugin(ElementBase):
            name = "plugin"
            namespace = "http://test/slash/bar"
            interfaces = set(('attrib',))

        register_stanza_plugin(TestStanza, TestSubStanza, iterable=True)
        register_stanza_plugin(TestStanza, TestStanzaPlugin)

        stanza = TestStanza()
        self.failUnless(stanza.match("foo"),
            "Stanza did not match its own tag name.")

        self.failUnless(stanza.match("{foo}foo"),
            "Stanza did not match its own namespaced name.")

        stanza['bar'] = 'a'
        self.failUnless(stanza.match("foo@bar=a"),
            "Stanza did not match its own name with attribute value check.")

        stanza['baz'] = 'b'
        self.failUnless(stanza.match("foo@bar=a@baz=b"),
            "Stanza did not match its own name with multiple attributes.")

        stanza['qux'] = 'c'
        self.failUnless(stanza.match("foo/qux"),
            "Stanza did not match with subelements.")

        stanza['qux'] = ''
        self.failUnless(stanza.match("foo/qux") == False,
            "Stanza matched missing subinterface element.")

        self.failUnless(stanza.match("foo/bar") == False,
            "Stanza matched nonexistent element.")

        stanza['plugin']['attrib'] = 'c'
        self.failUnless(stanza.match("foo/plugin@attrib=c"),
            "Stanza did not match with plugin and attribute.")

        self.failUnless(stanza.match("foo/{http://test/slash/bar}plugin"),
            "Stanza did not match with namespaced plugin.")

        substanza = TestSubStanza()
        substanza['attrib'] = 'd'
        stanza.append(substanza)
        self.failUnless(stanza.match("foo/sub@attrib=d"),
            "Stanza did not match with substanzas and attribute.")

        self.failUnless(stanza.match("foo/{baz}sub"),
            "Stanza did not match with namespaced substanza.")

    def testComparisons(self):
        """Test comparing ElementBase objects."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        stanza1 = TestStanza()
        stanza1['bar'] = 'a'

        self.failUnless(stanza1,
            "Stanza object does not evaluate to True")

        stanza2 = TestStanza()
        stanza2['baz'] = 'b'

        self.failUnless(stanza1 != stanza2,
            "Different stanza objects incorrectly compared equal.")

        stanza1['baz'] = 'b'
        stanza2['bar'] = 'a'

        self.failUnless(stanza1 == stanza2,
            "Equal stanzas incorrectly compared inequal.")

    def testKeys(self):
        """Test extracting interface names from a stanza object."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))
            plugin_attrib = 'qux'

        register_stanza_plugin(TestStanza, TestStanza)

        stanza = TestStanza()

        self.failUnless(set(stanza.keys()) == set(('lang', 'bar', 'baz')),
            "Returned set of interface keys does not match expected.")

        stanza.enable('qux')

        self.failUnless(set(stanza.keys()) == set(('lang', 'bar', 'baz', 'qux')),
            "Incorrect set of interface and plugin keys.")

    def testGet(self):
        """Test accessing stanza interfaces using get()."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        stanza = TestStanza()
        stanza['bar'] = 'a'

        self.failUnless(stanza.get('bar') == 'a',
            "Incorrect value returned by stanza.get")

        self.failUnless(stanza.get('baz', 'b') == 'b',
            "Incorrect default value returned by stanza.get")

    def testSubStanzas(self):
        """Test manipulating substanzas of a stanza object."""

        class TestSubStanza(ElementBase):
            name = "foobar"
            namespace = "foo"
            interfaces = set(('qux',))

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        register_stanza_plugin(TestStanza, TestSubStanza, iterable=True)

        stanza = TestStanza()
        substanza1 = TestSubStanza()
        substanza2 = TestSubStanza()
        substanza1['qux'] = 'a'
        substanza2['qux'] = 'b'

        # Test appending substanzas
        self.failUnless(len(stanza) == 0,
            "Incorrect empty stanza size.")

        stanza.append(substanza1)
        self.check(stanza, """
          <foo xmlns="foo">
            <foobar qux="a" />
          </foo>
        """, use_values=False)
        self.failUnless(len(stanza) == 1,
            "Incorrect stanza size with 1 substanza.")

        stanza.append(substanza2)
        self.check(stanza, """
          <foo xmlns="foo">
            <foobar qux="a" />
            <foobar qux="b" />
          </foo>
        """, use_values=False)
        self.failUnless(len(stanza) == 2,
            "Incorrect stanza size with 2 substanzas.")

        # Test popping substanzas
        stanza.pop(0)
        self.check(stanza, """
          <foo xmlns="foo">
            <foobar qux="b" />
          </foo>
        """, use_values=False)

        # Test iterating over substanzas
        stanza.append(substanza1)
        results = []
        for substanza in stanza:
            results.append(substanza['qux'])
        self.failUnless(results == ['b', 'a'],
            "Iteration over substanzas failed: %s." % str(results))

    def testCopy(self):
        """Test copying stanza objects."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        stanza1 = TestStanza()
        stanza1['bar'] = 'a'

        stanza2 = stanza1.__copy__()

        self.failUnless(stanza1 == stanza2,
            "Copied stanzas are not equal to each other.")

        stanza1['baz'] = 'b'
        self.failUnless(stanza1 != stanza2,
            "Divergent stanza copies incorrectly compared equal.")

    def testExtension(self):
        """Testing using is_extension."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        class TestExtension(ElementBase):
            name = 'extended'
            namespace = 'foo'
            plugin_attrib = name
            interfaces = set((name,))
            is_extension = True

            def set_extended(self, value):
                self.xml.text = value

            def get_extended(self):
                return self.xml.text

            def del_extended(self):
                self.parent().xml.remove(self.xml)

        register_stanza_plugin(TestStanza, TestExtension)

        stanza = TestStanza()
        stanza['extended'] = 'testing'

        self.check(stanza, """
          <foo xmlns="foo">
            <extended>testing</extended>
          </foo>
        """)

        self.failUnless(stanza['extended'] == 'testing',
                "Could not retrieve stanza extension value.")

        del stanza['extended']
        self.check(stanza, """
          <foo xmlns="foo" />
        """)

    def testOverrides(self):
        """Test using interface overrides."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(('bar', 'baz'))

        class TestOverride(ElementBase):
            name = 'overrider'
            namespace = 'foo'
            plugin_attrib = name
            interfaces = set(('bar',))
            overrides = ['set_bar']

            def setup(self, xml):
                # Don't create XML for the plugin
                self.xml = ET.Element('')

            def set_bar(self, value):
                if not value.startswith('override-'):
                    self.parent()._set_attr('bar', 'override-%s' % value)
                else:
                    self.parent()._set_attr('bar', value)

        stanza = TestStanza()
        stanza['bar'] = 'foo'
        self.check(stanza, """
          <foo xmlns="foo" bar="foo" />
        """)

        register_stanza_plugin(TestStanza, TestOverride, overrides=True)

        stanza = TestStanza()
        stanza['bar'] = 'foo'
        self.check(stanza, """
          <foo xmlns="foo" bar="override-foo" />
        """)

    def testBoolInterfaces(self):
        """Test using boolean interfaces."""

        class TestStanza(ElementBase):
            name = "foo"
            namespace = "foo"
            interfaces = set(['bar'])
            bool_interfaces = interfaces

        stanza = TestStanza()
        self.check(stanza, """
          <foo xmlns="foo" />
        """)

        self.assertFalse(stanza['bar'],
                "Returned True for missing bool interface element.")

        stanza['bar'] = True
        self.check(stanza, """
          <foo xmlns="foo">
            <bar />
          </foo>
        """)

        self.assertTrue(stanza['bar'],
                "Returned False for present bool interface element.")

        stanza['bar'] = False
        self.check(stanza, """
          <foo xmlns="foo" />
        """)

    def testGetMultiAttrib(self):
        """Test retrieving multi_attrib substanzas."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'foo'
            interfaces = set()

        class TestMultiStanza1(ElementBase):
            name = 'bar'
            namespace = 'bar'
            plugin_attrib = name
            plugin_multi_attrib = 'bars'

        class TestMultiStanza2(ElementBase):
            name = 'baz'
            namespace = 'baz'
            plugin_attrib = name
            plugin_multi_attrib = 'bazs'

        register_stanza_plugin(TestStanza, TestMultiStanza1, iterable=True)
        register_stanza_plugin(TestStanza, TestMultiStanza2, iterable=True)

        stanza = TestStanza()
        stanza.append(TestMultiStanza1())
        stanza.append(TestMultiStanza2())
        stanza.append(TestMultiStanza1())
        stanza.append(TestMultiStanza2())

        self.check(stanza, """
          <foo xmlns="foo">
            <bar xmlns="bar" />
            <baz xmlns="baz" />
            <bar xmlns="bar" />
            <baz xmlns="baz" />
          </foo>
        """, use_values=False)

        bars = stanza['bars']
        bazs = stanza['bazs']

        for bar in bars:
            self.check(bar, """
              <bar xmlns="bar" />
            """)

        for baz in bazs:
            self.check(baz, """
              <baz xmlns="baz" />
            """)

        self.assertEqual(len(bars), 2,
                "Wrong number of <bar /> stanzas: %s" % len(bars))
        self.assertEqual(len(bazs), 2,
                "Wrong number of <baz /> stanzas: %s" % len(bazs))

    def testSetMultiAttrib(self):
        """Test setting multi_attrib substanzas."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'foo'
            interfaces = set()

        class TestMultiStanza1(ElementBase):
            name = 'bar'
            namespace = 'bar'
            plugin_attrib = name
            plugin_multi_attrib = 'bars'

        class TestMultiStanza2(ElementBase):
            name = 'baz'
            namespace = 'baz'
            plugin_attrib = name
            plugin_multi_attrib = 'bazs'

        register_stanza_plugin(TestStanza, TestMultiStanza1, iterable=True)
        register_stanza_plugin(TestStanza, TestMultiStanza2, iterable=True)

        stanza = TestStanza()
        stanza['bars'] = [TestMultiStanza1(), TestMultiStanza1()]
        stanza['bazs'] = [TestMultiStanza2(), TestMultiStanza2()]

        self.check(stanza, """
          <foo xmlns="foo">
            <bar xmlns="bar" />
            <bar xmlns="bar" />
            <baz xmlns="baz" />
            <baz xmlns="baz" />
          </foo>
        """, use_values=False)

        self.assertEqual(len(stanza['substanzas']), 4,
            "Wrong number of substanzas: %s" % len(stanza['substanzas']))

        stanza['bars'] = [TestMultiStanza1()]

        self.check(stanza, """
          <foo xmlns="foo">
            <baz xmlns="baz" />
            <baz xmlns="baz" />
            <bar xmlns="bar" />
          </foo>
        """, use_values=False)

        self.assertEqual(len(stanza['substanzas']), 3,
            "Wrong number of substanzas: %s" % len(stanza['substanzas']))


    def testDelMultiAttrib(self):
        """Test deleting multi_attrib substanzas."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'foo'
            interfaces = set()

        class TestMultiStanza1(ElementBase):
            name = 'bar'
            namespace = 'bar'
            plugin_attrib = name
            plugin_multi_attrib = 'bars'

        class TestMultiStanza2(ElementBase):
            name = 'baz'
            namespace = 'baz'
            plugin_attrib = name
            plugin_multi_attrib = 'bazs'

        register_stanza_plugin(TestStanza, TestMultiStanza1, iterable=True)
        register_stanza_plugin(TestStanza, TestMultiStanza2, iterable=True)

        stanza = TestStanza()
        bars = [TestMultiStanza1(), TestMultiStanza1()]
        bazs = [TestMultiStanza2(), TestMultiStanza2()]

        stanza['bars'] = bars
        stanza['bazs'] = bazs

        self.check(stanza, """
          <foo xmlns="foo">
            <bar xmlns="bar" />
            <bar xmlns="bar" />
            <baz xmlns="baz" />
            <baz xmlns="baz" />
          </foo>
        """, use_values=False)

        del stanza['bars']

        self.check(stanza, """
          <foo xmlns="foo">
            <baz xmlns="baz" />
            <baz xmlns="baz" />
          </foo>
        """, use_values=False)

        self.assertEqual(len(stanza['substanzas']), 2,
            "Wrong number of substanzas: %s" % len(stanza['substanzas']))

    def testDefaultLang(self):
        """Test setting a normal subinterface when a default language is set"""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'test'
            interfaces = set(['test'])
            sub_interfaces = interfaces
            lang_interfaces = interfaces

        stanza = TestStanza()
        stanza['lang'] = 'sv'
        stanza['test'] = 'hej'

        self.check(stanza, """
          <foo xmlns="test" xml:lang="sv">
            <test>hej</test>
          </foo>
        """)

        self.assertEqual(stanza['test'], 'hej',
                "Incorrect subinterface value: %s" % stanza['test'])

        self.assertEqual(stanza['test|sv'], 'hej',
                "Incorrect subinterface value: %s" % stanza['test|sv'])

    def testSpecifyLangWithDefault(self):
        """Test specifying various languages."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'test'
            interfaces = set(['test'])
            sub_interfaces = interfaces
            lang_interfaces = interfaces

        stanza = TestStanza()
        stanza['lang'] = 'sv'
        stanza['test'] = 'hej'
        stanza['test|en'] = 'hi'
        stanza['test|es'] = 'hola'

        self.check(stanza, """
          <foo xmlns="test" xml:lang="sv">
            <test>hej</test>
            <test xml:lang="en">hi</test>
            <test xml:lang="es">hola</test>
          </foo>
        """)

        self.assertEqual(stanza['test'], 'hej',
                "Incorrect subinterface value: %s" % stanza['test'])

        self.assertEqual(stanza['test|sv'], 'hej',
                "Incorrect subinterface value: %s" % stanza['test|sv'])

        self.assertEqual(stanza['test|en'], 'hi',
                "Incorrect subinterface value: %s" % stanza['test|en'])

        self.assertEqual(stanza['test|es'], 'hola',
                "Incorrect subinterface value: %s" % stanza['test|es'])

    def testSpecifyLangWithNoDefault(self):
        """Test specifying various languages."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'test'
            interfaces = set(['test'])
            sub_interfaces = interfaces
            lang_interfaces = interfaces

        stanza = TestStanza()
        stanza['test'] = 'hej'
        stanza['test|en'] = 'hi'
        stanza['test|es'] = 'hola'

        self.check(stanza, """
          <foo xmlns="test">
            <test>hej</test>
            <test xml:lang="en">hi</test>
            <test xml:lang="es">hola</test>
          </foo>
        """)

        self.assertEqual(stanza['test'], 'hej',
                "Incorrect subinterface value: %s" % stanza['test'])

        self.assertEqual(stanza['test|en'], 'hi',
                "Incorrect subinterface value: %s" % stanza['test|en'])

        self.assertEqual(stanza['test|es'], 'hola',
                "Incorrect subinterface value: %s" % stanza['test|es'])

    def testModifyLangInterfaceWithDefault(self):
        """Test resetting an interface when a default lang is used."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'test'
            interfaces = set(['test'])
            sub_interfaces = interfaces
            lang_interfaces = interfaces

        stanza = TestStanza()
        stanza['lang'] = 'es'
        stanza['test'] = 'hola'
        stanza['test|en'] = 'hi'

        self.check(stanza, """
          <foo xmlns="test" xml:lang="es">
            <test>hola</test>
            <test xml:lang="en">hi</test>
          </foo>
        """)

        stanza['test'] = 'adios'
        stanza['test|en'] = 'bye'

        self.check(stanza, """
          <foo xmlns="test" xml:lang="es">
            <test>adios</test>
            <test xml:lang="en">bye</test>
          </foo>
        """)

        self.assertEqual(stanza['test'], 'adios',
                "Incorrect subinterface value: %s" % stanza['test'])

        self.assertEqual(stanza['test|es'], 'adios',
                "Incorrect subinterface value: %s" % stanza['test|es'])

        self.assertEqual(stanza['test|en'], 'bye',
                "Incorrect subinterface value: %s" % stanza['test|en'])

        stanza['test|es'] = 'hola'

        self.check(stanza, """
          <foo xmlns="test" xml:lang="es">
            <test>hola</test>
            <test xml:lang="en">bye</test>
          </foo>
        """)

        self.assertEqual(stanza['test'], 'hola',
                "Incorrect subinterface value: %s" % stanza['test'])

        self.assertEqual(stanza['test|es'], 'hola',
                "Incorrect subinterface value: %s" % stanza['test|es'])

    def testModifyLangInterfaceWithNoDefault(self):
        """Test resetting an interface when no default lang is used."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'test'
            interfaces = set(['test'])
            sub_interfaces = interfaces
            lang_interfaces = interfaces

        stanza = TestStanza()
        stanza['test'] = 'hola'
        stanza['test|en'] = 'hi'

        self.check(stanza, """
          <foo xmlns="test">
            <test>hola</test>
            <test xml:lang="en">hi</test>
          </foo>
        """)

        stanza['test'] = 'adios'
        stanza['test|en'] = 'bye'

        self.check(stanza, """
          <foo xmlns="test">
            <test>adios</test>
            <test xml:lang="en">bye</test>
          </foo>
        """)

        self.assertEqual(stanza['test'], 'adios',
                "Incorrect subinterface value: %s" % stanza['test'])

        self.assertEqual(stanza['test'], 'adios',
                "Incorrect subinterface value: %s" % stanza['test|es'])

        self.assertEqual(stanza['test|en'], 'bye',
                "Incorrect subinterface value: %s" % stanza['test|en'])

    def testDelInterfacesWithDefaultLang(self):
        """Test deleting interfaces with a default lang set."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'test'
            interfaces = set(['test'])
            sub_interfaces = interfaces
            lang_interfaces = interfaces

        stanza = TestStanza()
        stanza['lang'] = 'en'
        stanza['test'] = 'hi'
        stanza['test|no'] = 'hej'
        stanza['test|fr'] = 'bonjour'

        self.check(stanza, """
          <foo xmlns="test" xml:lang="en">
            <test>hi</test>
            <test xml:lang="no">hej</test>
            <test xml:lang="fr">bonjour</test>
          </foo>
        """)

        del stanza['test']

        self.check(stanza, """
          <foo xmlns="test" xml:lang="en">
            <test xml:lang="no">hej</test>
            <test xml:lang="fr">bonjour</test>
          </foo>
        """)

        del stanza['test|no']

        self.check(stanza, """
          <foo xmlns="test" xml:lang="en">
            <test xml:lang="fr">bonjour</test>
          </foo>
        """)

    def testDelInterfacesWithNoDefaultLang(self):
        """Test deleting interfaces with no default lang set."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'test'
            interfaces = set(['test'])
            sub_interfaces = interfaces
            lang_interfaces = interfaces

        stanza = TestStanza()
        stanza['test'] = 'hi'
        stanza['test|no'] = 'hej'
        stanza['test|fr'] = 'bonjour'

        self.check(stanza, """
          <foo xmlns="test">
            <test>hi</test>
            <test xml:lang="no">hej</test>
            <test xml:lang="fr">bonjour</test>
          </foo>
        """)

        del stanza['test']

        self.check(stanza, """
          <foo xmlns="test">
            <test xml:lang="no">hej</test>
            <test xml:lang="fr">bonjour</test>
          </foo>
        """)

        del stanza['test|no']

        self.check(stanza, """
          <foo xmlns="test">
            <test xml:lang="fr">bonjour</test>
          </foo>
        """)

    def testStarLang(self):
        """Test using interface|*."""

        class TestStanza(ElementBase):
            name = 'foo'
            namespace = 'test'
            interfaces = set(['test'])
            sub_interfaces = interfaces
            lang_interfaces = interfaces

        data = OrderedDict()
        data['en'] = 'hi'
        data['fr'] = 'bonjour'
        data['no'] = 'hej'

        stanza = TestStanza()
        stanza['test|*'] = data

        self.check(stanza, """
          <foo xmlns="test">
            <test xml:lang="en">hi</test>
            <test xml:lang="fr">bonjour</test>
            <test xml:lang="no">hej</test>
          </foo>
        """)

        data2 = stanza['test|*']

        self.assertEqual(data, data2,
                "Did not extract expected language data: %s" % data2)

        del stanza['test|*']

        self.check(stanza, """
          <foo xmlns="test" />
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestElementBase)
