import unittest
import logging

from sleekxmpp.plugins.base import PluginManager, BasePlugin, register_plugin


class A(BasePlugin):
    name = 'a'


class B(BasePlugin):
    name = 'b'


class C(BasePlugin):
    name = 'c'
    dependencies = set(['b', 'd'])


class D(BasePlugin):
    name = 'd'
    dependencies = set(['c'])


class E(BasePlugin):
    name = 'e'
    dependencies = set(['a', 'd'])

class F(BasePlugin):
    name = 'f'
    dependencies = set(['a', 'b'])


register_plugin(A)
register_plugin(B)
register_plugin(C)
register_plugin(D)
register_plugin(E)
register_plugin(F)


class TestPlugins(unittest.TestCase):


    def test_enable(self):
        """Enable a single plugin."""
        p = PluginManager(None)

        events = []

        def init(self):
            events.append('init')

        A.plugin_init = init

        p.enable('a')

        self.assertEqual(len(p), 1, "Wrong number of enabled plugins.")
        self.assertEqual(events, ['init'], "Plugin init method not called.")

    def test_disable(self):
        """Disable a single plugin."""
        p = PluginManager(None)

        events = []

        def init(self):
            events.append('init')

        def end(self):
            events.append('end')

        A.plugin_init = init
        A.plugin_end = end

        p.enable('a')
        p.disable('a')

        self.assertEqual(len(p), 0, "Wrong number of enabled plugins.")
        self.assertEqual(events, ['init', 'end'], 
                "Plugin lifecycle methods not called.")

    def test_enable_dependencies(self):
        """Enable a plugin with acyclic dependencies."""
        p = PluginManager(None)

        events = []

        A.plugin_init = lambda s: events.append('init_a')
        B.plugin_init = lambda s: events.append('init_b')

        p.enable('f')

        self.assertEqual(len(p), 3, "Wrong number of enabled plugins.")
        self.assertTrue('init_a' in events, "Dependency A not enabled.")
        self.assertTrue('init_b' in events, "Dependency B not enabled.")

    def test_enable_cyclic_dependencies(self):
        """Enable a plugin with cyclic dependencies."""

        p = PluginManager(None)

        events = []

        B.plugin_init = lambda s: events.append('init_b')
        C.plugin_init = lambda s: events.append('init_c')
        D.plugin_init = lambda s: events.append('init_d')

        p.enable('c')

        self.assertEqual(len(p), 3, "Wrong number of enabled plugins.")
        self.assertTrue('init_b' in events, "Dependency B not enabled.")
        self.assertTrue('init_c' in events, "Dependency C not enabled.")
        self.assertTrue('init_d' in events, "Dependency D not enabled.")

    def test_disable_dependendents(self):
        """Disable a plugin with dependents."""

        p = PluginManager(None)

        events = []

        A.plugin_end = lambda s: events.append('end_a')
        B.plugin_end = lambda s: events.append('end_b')
        F.plugin_end = lambda s: events.append('end_f')

        p.enable('f')
        p.disable('a')

        self.assertEqual(len(p), 1, "Wrong number of enabled plugins.")
        self.assertTrue('end_f' in events, "Dependent F not disabled.")
        self.assertTrue('end_a' in events, "Plugin A not disabled.")

    def test_disable_cyclic_dependents(self):
        """Disable a plugin with cyclic dependents."""

        p = PluginManager(None)

        events = []

        B.plugin_end = lambda s: events.append('end_b')
        C.plugin_end = lambda s: events.append('end_c')
        D.plugin_end = lambda s: events.append('end_d')

        p.enable('c')
        p.disable('b')

        self.assertEqual(len(p), 0, "Wrong number of enabled plugins.")
        self.assertTrue('end_b' in events, "Plugin B not disabled.")
        self.assertTrue('end_c' in events, "Dependent C not disabled.")
        self.assertTrue('end_d' in events, "Dependent D not disabled.")



suite = unittest.TestLoader().loadTestsFromTestCase(TestPlugins)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    tests = unittest.TestSuite([suite])
    unittest.TextTestRunner(verbosity=2).run(tests)
