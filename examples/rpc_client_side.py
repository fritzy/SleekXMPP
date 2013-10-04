#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2011  Dann Martens
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from sleekxmpp.plugins.xep_0009.remote import Endpoint, remote, Remote, \
    ANY_ALL
import threading
import time

class Thermostat(Endpoint):

    def FQN(self):
        return 'thermostat'

    def __init__(self, initial_temperature):
        self._temperature = initial_temperature
        self._event = threading.Event()

    @remote
    def set_temperature(self, temperature):
        return NotImplemented

    @remote
    def get_temperature(self):
        return NotImplemented

    @remote(False)
    def release(self):
        return NotImplemented



def main():

    session = Remote.new_session('operator@xmpp.org/rpc', '*****')

    thermostat = session.new_proxy('thermostat@xmpp.org/rpc', Thermostat)

    print("Current temperature is %s" % thermostat.get_temperature())

    thermostat.set_temperature(20)

    time.sleep(10)

    session.close()

if __name__ == '__main__':
    main()

