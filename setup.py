#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Nathanael C. Fritz
# All Rights Reserved
#
# This software is licensed as described in the README.rst and LICENSE
# file, which you should have received as part of this distribution.

import sys
import codecs
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
with codecs.open('README.rst', 'r', encoding='UTF-8') as readme:
    LONG_DESCRIPTION = ''.join(readme)

CLASSIFIERS      = [ 'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2.6',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3.1',
                     'Programming Language :: Python :: 3.2',
                     'Programming Language :: Python :: 3.3',
                     'Topic :: Software Development :: Libraries :: Python Modules',
                   ]

packages     = [ 'sleekxmpp',
                 'sleekxmpp/stanza',
                 'sleekxmpp/test',
                 'sleekxmpp/roster',
                 'sleekxmpp/util',
                 'sleekxmpp/util/sasl',
                 'sleekxmpp/xmlstream',
                 'sleekxmpp/xmlstream/matcher',
                 'sleekxmpp/xmlstream/handler',
                 'sleekxmpp/plugins',
                 'sleekxmpp/plugins/xep_0004',
                 'sleekxmpp/plugins/xep_0004/stanza',
                 'sleekxmpp/plugins/xep_0009',
                 'sleekxmpp/plugins/xep_0009/stanza',
                 'sleekxmpp/plugins/xep_0012',
                 'sleekxmpp/plugins/xep_0013',
                 'sleekxmpp/plugins/xep_0016',
                 'sleekxmpp/plugins/xep_0020',
                 'sleekxmpp/plugins/xep_0027',
                 'sleekxmpp/plugins/xep_0030',
                 'sleekxmpp/plugins/xep_0030/stanza',
                 'sleekxmpp/plugins/xep_0033',
                 'sleekxmpp/plugins/xep_0047',
                 'sleekxmpp/plugins/xep_0048',
                 'sleekxmpp/plugins/xep_0049',
                 'sleekxmpp/plugins/xep_0050',
                 'sleekxmpp/plugins/xep_0054',
                 'sleekxmpp/plugins/xep_0059',
                 'sleekxmpp/plugins/xep_0060',
                 'sleekxmpp/plugins/xep_0060/stanza',
                 'sleekxmpp/plugins/xep_0065',
                 'sleekxmpp/plugins/xep_0066',
                 'sleekxmpp/plugins/xep_0071',
                 'sleekxmpp/plugins/xep_0077',
                 'sleekxmpp/plugins/xep_0078',
                 'sleekxmpp/plugins/xep_0080',
                 'sleekxmpp/plugins/xep_0084',
                 'sleekxmpp/plugins/xep_0085',
                 'sleekxmpp/plugins/xep_0086',
                 'sleekxmpp/plugins/xep_0091',
                 'sleekxmpp/plugins/xep_0092',
                 'sleekxmpp/plugins/xep_0095',
                 'sleekxmpp/plugins/xep_0096',
                 'sleekxmpp/plugins/xep_0107',
                 'sleekxmpp/plugins/xep_0108',
                 'sleekxmpp/plugins/xep_0115',
                 'sleekxmpp/plugins/xep_0118',
                 'sleekxmpp/plugins/xep_0122',
                 'sleekxmpp/plugins/xep_0128',
                 'sleekxmpp/plugins/xep_0131',
                 'sleekxmpp/plugins/xep_0152',
                 'sleekxmpp/plugins/xep_0153',
                 'sleekxmpp/plugins/xep_0172',
                 'sleekxmpp/plugins/xep_0184',
                 'sleekxmpp/plugins/xep_0186',
                 'sleekxmpp/plugins/xep_0191',
                 'sleekxmpp/plugins/xep_0196',
                 'sleekxmpp/plugins/xep_0198',
                 'sleekxmpp/plugins/xep_0199',
                 'sleekxmpp/plugins/xep_0202',
                 'sleekxmpp/plugins/xep_0203',
                 'sleekxmpp/plugins/xep_0221',
                 'sleekxmpp/plugins/xep_0224',
                 'sleekxmpp/plugins/xep_0231',
                 'sleekxmpp/plugins/xep_0235',
                 'sleekxmpp/plugins/xep_0249',
                 'sleekxmpp/plugins/xep_0257',
                 'sleekxmpp/plugins/xep_0258',
                 'sleekxmpp/plugins/xep_0279',
                 'sleekxmpp/plugins/xep_0280',
                 'sleekxmpp/plugins/xep_0297',
                 'sleekxmpp/plugins/xep_0308',
                 'sleekxmpp/plugins/xep_0313',
                 'sleekxmpp/plugins/xep_0319',
                 'sleekxmpp/plugins/xep_0323',
                 'sleekxmpp/plugins/xep_0323/stanza',
                 'sleekxmpp/plugins/xep_0325',
                 'sleekxmpp/plugins/xep_0325/stanza',
                 'sleekxmpp/plugins/xep_0332',
                 'sleekxmpp/plugins/xep_0332/stanza',
                 'sleekxmpp/plugins/google',
                 'sleekxmpp/plugins/google/gmail',
                 'sleekxmpp/plugins/google/auth',
                 'sleekxmpp/plugins/google/settings',
                 'sleekxmpp/plugins/google/nosave',
                 'sleekxmpp/features',
                 'sleekxmpp/features/feature_mechanisms',
                 'sleekxmpp/features/feature_mechanisms/stanza',
                 'sleekxmpp/features/feature_starttls',
                 'sleekxmpp/features/feature_bind',
                 'sleekxmpp/features/feature_session',
                 'sleekxmpp/features/feature_rosterver',
                 'sleekxmpp/features/feature_preapproval',
                 'sleekxmpp/thirdparty',
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
    requires     = [ 'dnspython', 'pyasn1', 'pyasn1_modules' ],
    classifiers  = CLASSIFIERS,
    cmdclass     = {'test': TestCommand}
)
