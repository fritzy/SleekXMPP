"""
"""

import sys
import hashlib


def bytes(text):
    """
    Convert Unicode text to UTF-8 encoded bytes.

    Since Python 2.6+ and Python 3+ have similar but incompatible
    signatures, this function unifies the two to keep code sane.

    :param text: Unicode text to convert to bytes
    :rtype: bytes (Python3), str (Python2.6+)
    """
    if sys.version_info < (3, 0):
        import __builtin__
        return __builtin__.bytes(text)
    else:
        import builtins
        if isinstance(text, builtins.bytes):
            # We already have bytes, so do nothing
            return text
        if isinstance(text, list):
            # Convert a list of integers to bytes
            return builtins.bytes(text)
        else:
            # Convert UTF-8 text to bytes
            return builtins.bytes(text, encoding='utf-8')


def quote(text):
    """
    Enclose in quotes and escape internal slashes and double quotes.

    :param text: A Unicode or byte string.
    """
    text = bytes(text)
    return b'"' + text.replace(b'\\', b'\\\\').replace(b'"', b'\\"') + b'"'


def num_to_bytes(num):
    """
    Convert an integer into a four byte sequence.

    :param integer num: An integer to convert to its byte representation.
    """
    bval = b''
    bval += bytes(chr(0xFF & (num >> 24)))
    bval += bytes(chr(0xFF & (num >> 16)))
    bval += bytes(chr(0xFF & (num >> 8)))
    bval += bytes(chr(0xFF & (num >> 0)))
    return bval


def bytes_to_num(bval):
    """
    Convert a four byte sequence to an integer.

    :param bytes bval: A four byte sequence to turn into an integer.
    """
    num = 0
    num += ord(bval[0] << 24)
    num += ord(bval[1] << 16)
    num += ord(bval[2] << 8)
    num += ord(bval[3])
    return num


def XOR(x, y):
    """
    Return the results of an XOR operation on two equal length byte strings.

    :param bytes x: A byte string
    :param bytes y: A byte string
    :rtype: bytes
    """
    result = b''
    for a, b in zip(x, y):
        if sys.version_info < (3, 0):
            result += chr((ord(a) ^ ord(b)))
        else:
            result += bytes([a ^ b])
    return result


def hash(name):
    """
    Return a hash function implementing the given algorithm.

    :param name: The name of the hashing algorithm to use.
    :type name: string

    :rtype: function
    """
    name = name.lower()
    if name.startswith('sha-'):
        name = 'sha' + name[4:]
    if name in dir(hashlib):
        return getattr(hashlib, name)
    return None


def hashes():
    """
    Return a list of available hashing algorithms.

    :rtype: list of strings
    """
    t = []
    if 'md5' in dir(hashlib):
        t = ['MD5']
    if 'md2' in dir(hashlib):
        t += ['MD2']
    hashes = ['SHA-' + h[3:] for h in dir(hashlib) if h.startswith('sha')]
    return t + hashes
