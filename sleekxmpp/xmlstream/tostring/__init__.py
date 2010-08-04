"""

"""

import sys


# Import the correct ToString class based on the Python version.
if sys.version_info < (3, 0):
    from sleekxmpp.xmlstream.tostring.tostring26 import ToString
else:
    from sleekxmpp.xmlstream.tostring.tostring import ToString

__all__ = ['ToString']
