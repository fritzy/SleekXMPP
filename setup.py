#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Nathanael C. Fritz
# All Rights Reserved
#
# This software is licensed as described in the README.rst and LICENSE
# file, which you should have received as part of this distribution.

import sys
try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command
# from ez_setup import use_setuptools

from testall import TestCommand
from sleekxmpp.version import __version__
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

VERSION          = __version__
DESCRIPTION      = 'SleekXMPP is an elegant Python library for XMPP (aka Jabber, Google Talk, etc).'
with open('README.rst') as readme:
    LONG_DESCRIPTION = ''.join(readme)

CLASSIFIERS      = [ 'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2.6',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3.1',
                     'Programming Language :: Python :: 3.2',
                     'Topic :: Software Development :: Libraries :: Python Modules',
                   ]

packages     = [ 'sleekxmpp',
                 'sleekxmpp/stanza',
                 'sleekxmpp/test',
                 'sleekxmpp/roster',
                 'sleekxmpp/xmlstream',
                 'sleekxmpp/xmlstream/matcher',
                 'sleekxmpp/xmlstream/handler',
                 'sleekxmpp/plugins',
                 'sleekxmpp/plugins/xep_0004',
                 'sleekxmpp/plugins/xep_0004/stanza',
                 'sleekxmpp/plugins/xep_0009',
                 'sleekxmpp/plugins/xep_0009/stanza',
                 'sleekxmpp/plugins/xep_0030',
                 'sleekxmpp/plugins/xep_0030/stanza',
                 'sleekxmpp/plugins/xep_0050',
                 'sleekxmpp/plugins/xep_0059',
                 'sleekxmpp/plugins/xep_0060',
                 'sleekxmpp/plugins/xep_0060/stanza',
                 'sleekxmpp/plugins/xep_0066',
                 'sleekxmpp/plugins/xep_0078',
                 'sleekxmpp/plugins/xep_0085',
                 'sleekxmpp/plugins/xep_0086',
                 'sleekxmpp/plugins/xep_0092',
                 'sleekxmpp/plugins/xep_0128',
                 'sleekxmpp/plugins/xep_0199',
                 'sleekxmpp/plugins/xep_0202',
                 'sleekxmpp/plugins/xep_0203',
                 'sleekxmpp/plugins/xep_0224',
                 'sleekxmpp/plugins/xep_0249',
                 'sleekxmpp/features',
                 'sleekxmpp/features/feature_mechanisms',
                 'sleekxmpp/features/feature_mechanisms/stanza',
                 'sleekxmpp/features/feature_starttls',
                 'sleekxmpp/features/feature_bind',
                 'sleekxmpp/features/feature_session',
                 'sleekxmpp/thirdparty',
                 'sleekxmpp/thirdparty/suelta',
                 'sleekxmpp/thirdparty/suelta/mechanisms',
                 ]

setup(
    name             = "sleekxmpp",
    version          = VERSION,
    description      = DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    author       = 'Nathanael Fritz',
    author_email = 'fritzy [at] netflint.net',
    url          = 'http://github.com/fritzy/SleekXMPP',
    license      = 'MIT',
    platforms    = [ 'any' ],
    packages     = packages,
    requires     = [ 'dnspython' ],
    classifiers  = CLASSIFIERS,
    cmdclass     = {'test': TestCommand}
)
