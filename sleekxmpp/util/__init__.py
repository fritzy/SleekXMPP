# -*- coding: utf-8 -*-
"""
    sleekxmpp.util
    ~~~~~~~~~~~~~~

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2012 Nathanael C. Fritz, Lance J.T. Stout
    :license: MIT, see LICENSE for more details
"""


from sleekxmpp.util.misc_ops import bytes, unicode, hashes, hash, \
                                    num_to_bytes, bytes_to_num, quote, \
                                    XOR, safedict


# =====================================================================
# Standardize import of Queue class:

import sys

def _gevent_threads_enabled():
    if not 'gevent' in sys.modules:
        return False
    try:
        from gevent import thread as green_thread
        thread = __import__('thread')
        return thread.LockType is green_thread.LockType
    except ImportError:
        return False

if _gevent_threads_enabled():
    import gevent.queue as queue
    _queue = queue.JoinableQueue
else:
    try:
        import queue
    except ImportError:
        import Queue as queue
    _queue = queue.Queue
class Queue(_queue):
    def put(self, item, block=True, timeout=None):
        if _queue.full(self):
            _queue.get(self)
        return _queue.put(self, item, block, timeout)

QueueEmpty = queue.Empty
