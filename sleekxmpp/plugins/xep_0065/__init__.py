from sleekxmpp.plugins.base import register_plugin

from sleekxmpp.plugins.xep_0065.stanza import Socks5
from sleekxmpp.plugins.xep_0065.proxy import XEP_0065


register_plugin(XEP_0065)
