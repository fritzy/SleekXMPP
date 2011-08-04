"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""
__all__ = ['xep_0004', 'xep_0009', 'xep_0012', 'xep_0030', 'xep_0033',
           'xep_0045', 'xep_0050', 'xep_0060', 'xep_0066', 'xep_0085',
           'xep_0086', 'xep_0092', 'xep_0128', 'xep_0199', 'xep_0203',
           'xep_0224', 'xep_0249', 'gmail_notify']

# Some plugins may require external dependencies beyond what the
# core SleekXMPP installation requires. Thus they should only by
# imported automatically if those dependecies are met.

HAVE_DATEUTIL = True
try:
    import dateutil
except:
    HAVE_DATEUTIL = False

if HAVE_DATEUTIL:
    __all__.append('xep_0082')
    __all__.append('xep_0202')
