# -*- coding: utf-8 -*-
"""
    sleekxmpp.xmlstream.scheduler
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a task scheduler that works better
    with SleekXMPP's threading usage than the stock version.

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

import time
import threading
import logging
import itertools

from sleekxmpp.util import Queue, QueueEmpty


#: The time in seconds to wait for events from the event queue, and also the
#: time between checks for the process stop signal.
WAIT_TIMEOUT = 1.0


log = logging.getLogger(__name__)


class Task(object):

    """
    A scheduled task that will be executed by the scheduler
    after a given time interval has passed.

    :param string name: The name of the task.
    :param int seconds: The number of seconds to wait before executing.
    :param callback: The function to execute.
    :param tuple args: The arguments to pass to the callback.
    :param dict kwargs: The keyword arguments to pass to the callback.
    :param bool repeat: Indicates if the task should repeat.
                        Defaults to ``False``.
    :param pointer: A pointer to an event queue for queuing callback
                    execution instead of executing immediately.
    """

    def __init__(self, name, seconds, callback, args=None,
                 kwargs=None, repeat=False, qpointer=None):
        #: The name of the task.
        self.name = name

        #: The number of seconds to wait before executing.
        self.seconds = seconds

        #: The function to execute once enough time has passed.
        self.callback = callback

        #: The arguments to pass to :attr:`callback`.
        self.args = args or tuple()

        #: The keyword arguments to pass to :attr:`callback`.
        self.kwargs = kwargs or {}

        #: Indicates if the task should repeat after executing,
        #: using the same :attr:`seconds` delay.
        self.repeat = repeat

        #: The time when the task should execute next.
        self.next = time.time() + self.seconds

        #: The main event queue, which allows for callbacks to
        #: be queued for execution instead of executing immediately.
        self.qpointer = qpointer

    def run(self):
        """Execute the task's callback.

        If an event queue was supplied, place the callback in the queue;
        otherwise, execute the callback immediately.
        """
        if self.qpointer is not None:
            self.qpointer.put(('schedule', self.callback,
                               self.args, self.kwargs, self.name))
        else:
            self.callback(*self.args, **self.kwargs)
        self.reset()
        return self.repeat

    def reset(self):
        """Reset the task's timer so that it will repeat."""
        self.next = time.time() + self.seconds


class Scheduler(object):

    """
    A threaded scheduler that allows for updates mid-execution unlike the
    scheduler in the standard library.

    Based on: http://docs.python.org/library/sched.html#module-sched

    :param parentstop: An :class:`~threading.Event` to signal stopping
                       the scheduler.
    """

    def __init__(self, parentstop=None):
        #: A queue for storing tasks
        self.addq = Queue()

        #: A list of tasks in order of execution time.
        self.schedule = []

        #: If running in threaded mode, this will be the thread processing
        #: the schedule.
        self.thread = None

        #: A flag indicating that the scheduler is running.
        self.run = False

        #: An :class:`~threading.Event` instance for signalling to stop
        #: the scheduler.
        self.stop = parentstop

        #: Lock for accessing the task queue.
        self.schedule_lock = threading.RLock()

        #: The time in seconds to wait for events from the event queue,
        #: and also the time between checks for the process stop signal.
        self.wait_timeout = WAIT_TIMEOUT

    def process(self, threaded=True, daemon=False):
        """Begin accepting and processing scheduled tasks.

        :param bool threaded: Indicates if the scheduler should execute
                              in its own thread. Defaults to ``True``.
        """
        if threaded:
            self.thread = threading.Thread(name='scheduler_process',
                                           target=self._process)
            self.thread.daemon = daemon
            self.thread.start()
        else:
            self._process()

    def _process(self):
        """Process scheduled tasks."""
        self.run = True
        try:
            while self.run and not self.stop.is_set():
                updated = False
                if self.schedule:
                    wait = self.schedule[0].next - time.time()
                else:
                    wait = self.wait_timeout
                try:
                    if wait <= 0.0:
                        newtask = self.addq.get(False)
                    else:
                        newtask = None
                        while self.run and \
                              not self.stop.is_set() and \
                              newtask is None and \
                              wait > 0:
                            try:
                                newtask = self.addq.get(True, min(wait, self.wait_timeout))
                            except QueueEmpty:          # Nothing to add, nothing to do. Check run flags and continue waiting.
                                wait -= self.wait_timeout
                except QueueEmpty:                      # Time to run some tasks, and no new tasks to add.
                    self.schedule_lock.acquire()
                    # select only those tasks which are to be executed now
                    relevant = itertools.takewhile(
                        lambda task: time.time() >= task.next, self.schedule)
                    # run the tasks and keep the return value in a tuple
                    status = map(lambda task: (task, task.run()), relevant)
                    # remove non-repeating tasks
                    for task, doRepeat in status:
                        if not doRepeat:
                            try:
                                self.schedule.remove(task)
                            except ValueError:
                                pass
                        else:
                            # only need to resort tasks if a repeated task has
                            # been kept in the list.
                            updated = True
                else:                                   # Add new task
                    self.schedule_lock.acquire()
                    if newtask is not None:
                        self.schedule.append(newtask)
                        updated = True
                finally:
                    if updated:
                        self.schedule.sort(key=lambda task: task.next)
                    self.schedule_lock.release()
        except KeyboardInterrupt:
            self.run = False
        except SystemExit:
            self.run = False
        log.debug("Quitting Scheduler thread")

    def add(self, name, seconds, callback, args=None,
            kwargs=None, repeat=False, qpointer=None):
        """Schedule a new task.

        :param string name: The name of the task.
        :param int seconds: The number of seconds to wait before executing.
        :param callback: The function to execute.
        :param tuple args: The arguments to pass to the callback.
        :param dict kwargs: The keyword arguments to pass to the callback.
        :param bool repeat: Indicates if the task should repeat.
                            Defaults to ``False``.
        :param pointer: A pointer to an event queue for queuing callback
                        execution instead of executing immediately.
        """
        try:
            self.schedule_lock.acquire()
            for task in self.schedule:
                if task.name == name:
                    raise ValueError("Key %s already exists" % name)

            self.addq.put(Task(name, seconds, callback, args,
                               kwargs, repeat, qpointer))
        except:
            raise
        finally:
            self.schedule_lock.release()

    def remove(self, name):
        """Remove a scheduled task ahead of schedule, and without
        executing it.

        :param string name: The name of the task to remove.
        """
        try:
            self.schedule_lock.acquire()
            the_task = None
            for task in self.schedule:
                if task.name == name:
                    the_task = task
            if the_task is not None:
                self.schedule.remove(the_task)
        except:
            raise
        finally:
            self.schedule_lock.release()

    def quit(self):
        """Shutdown the scheduler."""
        self.run = False
