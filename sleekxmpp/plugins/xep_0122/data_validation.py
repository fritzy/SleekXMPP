from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.xep_0004 import stanza
from sleekxmpp.plugins.xep_0004.stanza import FormField
from sleekxmpp.plugins.xep_0122.stanza import FormValidation


class XEP_0122(BasePlugin):
    """
    XEP-0004: Data Forms
    """

    name = 'xep_0122'
    description = 'XEP-0122: Data Forms Validation'
    dependencies = set(['xep_0004'])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(FormField, FormValidation)
