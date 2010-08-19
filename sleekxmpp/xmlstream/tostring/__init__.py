"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sys

# Import the correct tostring and xml_escape functions based on the Python
# version in order to properly handle Unicode.

if sys.version_info < (3, 0):
    from sleekxmpp.xmlstream.tostring.tostring26 import tostring, xml_escape
else:
    from sleekxmpp.xmlstream.tostring.tostring import tostring, xml_escape

__all__ = ['tostring', 'xml_escape']
