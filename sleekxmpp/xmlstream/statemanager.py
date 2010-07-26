"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

from __future__ import with_statement
import threading


class StateError(Exception):
    """Raised whenever a state transition was attempted but failed."""


class StateManager(object):
    """
    At the very core of SleekXMPP there is a need to track various 
    library configuration settings, XML stream features, and the 
    network connection status. The state manager is responsible for 
    tracking this information in a thread-safe manner.

    State 'variables' store the current state of these items as simple 
    string values or booleans. Changing those values must be done
    according to transitions defined when creating the state variable.

    If a state variable is given a value that is not allowed according
    to the transition definitions, a StateError is raised. When a
    valid value is assigned an event is raised named:
    
    _state_changed_nameofthestatevariable
    
    The event carries a dictionary containing the previous and the new
    state values.
    """
    
    def __init__(self, event_func=None):
        """
        Initialize the state manager. The parameter event_func should be
        the event() method of a SleekXMPP object in order to enable
        _state_changed_* events.
        """
        self.main_lock = threading.Lock()
	self.locks = {}
        self.state_variables = {}

        if event_func is not None:
            self.event = event_func
        else:
            self.event = lambda name, data: None

    def add(self, name, default=False, values=None, transitions=None):
        """
        Create a new state variable.

        When transitions is specified, only those defined state change
        transitions will be allowed.

        When values is specified (and not transitions), any state changes
        between those values are allowed.

        If neither values nor transitions are defined, then the state variable
        will be a binary switch between True and False.
        """
        if name in self.state_variables:
            raise IndexError("State variable %s already exists" % name)

        self.locks[name] = threading.Lock()
        with self.locks[name]:
            var = {'value': default,
                   'default': default,
                   'transitions': {}}
                
            if transitions is not None:
                for start in transitions:
                    var['transitions'][start] = set(transitions[start])
            elif values is not None:
                values = set(values)
                for value in values:
                    var['transitions'][value] = values
            elif values is None:
                var['transitions'] = {True: [False],
                                      False: [True]}

            self.state_variables[name] = var

    def addStates(self, var_defs):
        """
        Create multiple state variables at once.
        """
        for var, data in var_defs:
            self.add(var, 
                     default=data.get('default', False),
                     values=data.get('values', None),
                     transitions=data.get('transitions', None))

    def force_set(self, name, val):
        """
        Force setting a state variable's value by overriding transition checks.
        """
        with self.locks[name]:
            self.state_variables[name]['value'] = val

    def reset(self, name):
        """
        Reset a state variable to its default value.
        """
        with self.locks[name]:
            default = self.state_variables[name]['default']
            self.state_variables[name]['value'] = default

    def __getitem__(self, name):
        """
        Get the value of a state variable if it exists.
        """
        with self.locks[name]:
            if name not in self.state_variables:
                raise IndexError("State variable %s does not exist" % name)
            return self.state_variables[name]['value']

    def __setitem__(self, name, val):
        """
        Attempt to set the value of a state variable, but raise StateError
        if the transition is undefined.

        A _state_changed_* event is triggered after a successful transition.
        """
        with self.locks[name]:
            if name not in self.state_variables:
                raise IndexError("State variable %s does not exist" % name)
            current = self.state_variables[name]['value']
            if current == val:
                return
            if val in self.state_variables[name]['transitions'][current]:
                self.state_variables[name]['value'] = val
                self.event('_state_changed_%s' % name, {'from': current, 'to': val})
            else:
                raise StateError("Can not transition from '%s' to '%s'" % (str(current), str(val)))
