"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from __future__ import with_statement
import threading

class StateMachine(object):

	def __init__(self, states=[], groups=[]):
		self.lock = threading.Lock()
		self.__state = {}
		self.__default_state = {}
		self.__group = {}
		self.addStates(states)
		self.addGroups(groups)
	
	def addStates(self, states):
		with self.lock:
			for state in states:
				if state in self.__state or state in self.__group:
					raise IndexError("The state or group '%s' is already in the StateMachine." % state)
				self.__state[state] = states[state]
				self.__default_state[state] = states[state]
	
	def addGroups(self, groups):
		with self.lock:
			for gstate in groups:
				if gstate in self.__state or gstate in self.__group:
					raise IndexError("The key or group '%s' is already in the StateMachine." % gstate)
				for state in groups[gstate]:
					if state in self.__state:
						raise IndexError("The group %s contains a key %s which is not set in the StateMachine." % (gstate, state))
				self.__group[gstate] = groups[gstate]
	
	def set(self, state, status):
		with self.lock:
			if state in self.__state:
				self.__state[state] = bool(status)
			else:
				raise KeyError("StateMachine does not contain state %s." % state)
	
	def __getitem__(self, key):
		if key in self.__group:
			for state in self.__group[key]:
				if not self.__state[state]:
					return False
			return True
		return self.__state[key]
	
	def __getattr__(self, attr):
		return self.__getitem__(attr)
	
	def reset(self):
		self.__state = self.__default_state

