"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.plugins.base import PluginManager, PluginNotFound, BasePlugin
from sleekxmpp.plugins.base import register_plugin, load_plugin


__all__ = [
    # Non-standard
    'gmail_notify',  # Gmail searching and notifications

    # XEPS
    'xep_0004',  # Data Forms
    'xep_0009',  # Jabber-RPC
    'xep_0012',  # Last Activity
    'xep_0030',  # Service Discovery
    'xep_0033',  # Extended Stanza Addresses
    'xep_0045',  # Multi-User Chat (Client)
    'xep_0047',  # In-Band Bytestreams
    'xep_0050',  # Ad-hoc Commands
    'xep_0059',  # Result Set Management
    'xep_0060',  # Pubsub (Client)
    'xep_0066',  # Out of Band Data
    'xep_0077',  # In-Band Registration
#   'xep_0078',  # Non-SASL auth. Don't automatically load
    'xep_0080',  # User Location
    'xep_0082',  # XMPP Date and Time Profiles
    'xep_0085',  # Chat State Notifications
    'xep_0086',  # Legacy Error Codes
    'xep_0092',  # Software Version
    'xep_0107',  # User Mood
    'xep_0108',  # User Activity
    'xep_0115',  # Entity Capabilities
    'xep_0118',  # User Tune
    'xep_0128',  # Extended Service Discovery
    'xep_0163',  # Personal Eventing Protocol
    'xep_0172',  # User Nickname
    'xep_0184',  # Message Receipts
    'xep_0199',  # Ping
    'xep_0202',  # Entity Time
    'xep_0203',  # Delayed Delivery
    'xep_0224',  # Attention
    'xep_0249',  # Direct MUC Invitations
]
