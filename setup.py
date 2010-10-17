#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Nathanael C. Fritz
# All Rights Reserved
#
# This software is licensed as described in the README file,
# which you should have received as part of this distribution.
#

# from ez_setup import use_setuptools
from distutils.core import setup
import sys

# if 'cygwin' in sys.platform.lower():
#     min_version = '0.6c6'
# else:
#     min_version = '0.6a9'
#
# try:
#     use_setuptools(min_version=min_version)
# except TypeError:
#     # locally installed ez_setup won't have min_version
#     use_setuptools()
#
# from setuptools import setup, find_packages, Extension, Feature

VERSION          = '1.0.0.0'
DESCRIPTION      = 'SleekXMPP is an elegant Python library for XMPP (aka Jabber, Google Talk, etc).'
LONG_DESCRIPTION = """
SleekXMPP is an elegant Python library for XMPP (aka Jabber, Google Talk, etc).
"""

CLASSIFIERS      = [ 'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT',
                     'Programming Language :: Python',
                     'Topic :: Software Development :: Libraries :: Python Modules',
                   ]

packages     = [ 'sleekxmpp',
                 'sleekxmpp/plugins',
                 'sleekxmpp/stanza',
                 'sleekxmpp/test',
                 'sleekxmpp/xmlstream',
                 'sleekxmpp/xmlstream/matcher',
                 'sleekxmpp/xmlstream/handler',
                 'sleekxmpp/thirdparty',
                 ]

if sys.version_info < (3, 0):
    py_modules = ['sleekxmpp.xmlstream.tostring.tostring26']
else:
    py_modules = ['sleekxmpp.xmlstream.tostring.tostring']

setup(
    name             = "sleekxmpp",
    version          = VERSION,
    description      = DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    author       = 'Nathanael Fritz',
    author_email = 'fritzy [at] netflint.net',
    url          = 'http://code.google.com/p/sleekxmpp',
    license      = 'MIT',
    platforms    = [ 'any' ],
    packages     = packages,
    py_modules   = py_modules,
    requires     = [ 'tlslite', 'pythondns' ],
    )

