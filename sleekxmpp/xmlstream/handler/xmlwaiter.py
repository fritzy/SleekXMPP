"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from . waiter import Waiter

class XMLWaiter(Waiter):
	
	def prerun(self, payload):
		Waiter.prerun(self, payload.xml)
