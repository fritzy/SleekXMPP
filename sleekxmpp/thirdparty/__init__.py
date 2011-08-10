try:
    from collections import OrderedDict
except:
    from sleekxmpp.thirdparty.ordereddict import OrderedDict

from sleekxmpp.thirdparty import suelta
from sleekxmpp.thirdparty.mini_dateutil import tzutc, tzoffset, parse_iso
