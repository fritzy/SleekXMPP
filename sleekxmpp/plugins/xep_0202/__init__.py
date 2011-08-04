"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
import sleekxmpp


log = logging.getLogger(__name__)


HAVE_DATEUTIL = True
try:
    import dateutil
except:
    HAVE_DATEUTIL = False


if HAVE_DATEUTIL:
    from sleekxmpp.plugins.xep_0202 import stanza
    from sleekxmpp.plugins.xep_0202.stanza import EntityTime
    from sleekxmpp.plugins.xep_0202.time import xep_0202
else:
    log.warning("XEP-0202 requires the dateutil package")
