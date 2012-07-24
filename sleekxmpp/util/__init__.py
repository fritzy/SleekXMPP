# -*- coding: utf-8 -*-
"""
    sleekxmpp.util
    ~~~~~~~~~~~~~~

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2012 Nathanael C. Fritz, Lance J.T. Stout
    :license: MIT, see LICENSE for more details
"""


# =====================================================================
# Standardize import of Queue class:

try:
    import queue
except ImportError:
    import Queue as queue


Queue = queue.Queue
QueueEmpty = queue.Empty
