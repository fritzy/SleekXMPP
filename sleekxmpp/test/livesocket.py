"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import socket
try:
    import queue
except ImportError:
    import Queue as queue


class TestLiveSocket(object):

    """
    A live test socket that reads and writes to queues in
    addition to an actual networking socket.

    Methods:
        next_sent -- Return the next sent stanza.
        next_recv -- Return the next received stanza.
        recv_data -- Dummy method to have same interface as TestSocket.
        recv      -- Read the next stanza from the socket.
        send      -- Write a stanza to the socket.
        makefile  -- Dummy call, returns self.
        read      -- Read the next stanza from the socket.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new, live test socket.

        Arguments:
            Same as arguments for socket.socket
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv_buffer = []
        self.recv_queue = queue.Queue()
        self.send_queue = queue.Queue()
        self.is_live = True

    def __getattr__(self, name):
        """
        Return attribute values of internal, live socket.

        Arguments:
            name -- Name of the attribute requested.
        """

        return getattr(self.socket, name)

    # ------------------------------------------------------------------
    # Testing Interface

    def next_sent(self, timeout=None):
        """
        Get the next stanza that has been sent.

        Arguments:
            timeout -- Optional timeout for waiting for a new value.
        """
        args = {'block': False}
        if timeout is not None:
            args = {'block': True, 'timeout': timeout}
        try:
            return self.send_queue.get(**args)
        except:
            return None

    def next_recv(self, timeout=None):
        """
        Get the next stanza that has been received.

        Arguments:
            timeout -- Optional timeout for waiting for a new value.
        """
        args = {'block': False}
        if timeout is not None:
            args = {'block': True, 'timeout': timeout}
        try:
            if self.recv_buffer:
                return self.recv_buffer.pop(0)
            else:
                return self.recv_queue.get(**args)
        except:
            return None

    def recv_data(self, data):
        """
        Add data to a receive buffer for cases when more than a single stanza
        was received.
        """
        self.recv_buffer.append(data)

    # ------------------------------------------------------------------
    # Socket Interface

    def recv(self, *args, **kwargs):
        """
        Read data from the socket.

        Store a copy in the receive queue.

        Arguments:
            Placeholders. Same as for socket.recv.
        """
        data = self.socket.recv(*args, **kwargs)
        self.recv_queue.put(data)
        return data

    def send(self, data):
        """
        Send data on the socket.

        Store a copy in the send queue.

        Arguments:
            data -- String value to write.
        """
        self.send_queue.put(data)
        self.socket.send(data)

    # ------------------------------------------------------------------
    # File Socket

    def makefile(self, *args, **kwargs):
        """
        File socket version to use with ElementTree.

        Arguments:
            Placeholders, same as socket.makefile()
        """
        return self

    def read(self, *args, **kwargs):
        """
        Implement the file socket read interface.

        Arguments:
            Placeholders, same as socket.recv()
        """
        return self.recv(*args, **kwargs)
