"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
import threading
from . callback import Callback

class XMLCallback(Callback):
	
	def run(self, payload, instream=False):
		Callback.run(self, payload.xml, instream)
