try:
	import queue
except ImportError:
	import Queue as queue
import time
import threading

class Task(object):
	"""Task object for the Scheduler class"""
	def __init__(self, name, seconds, callback, args=None, kwargs=None, repeat=False, qpointer=None):
		self.name = name
		self.seconds = seconds
		self.callback = callback
		self.args = args or tuple()
		self.kwargs = kwargs or {}
		self.repeat = repeat
		self.next = time.time() + self.seconds
		self.qpointer = qpointer
	
	def run(self):
		if self.qpointer is not None:
			self.qpointer.put(('schedule', self.callback, self.args))
		else:
			self.callback(*self.args, **self.kwargs)
		self.reset()
		return self.repeat
	
	def reset(self):
		self.next = time.time() + self.seconds

class Scheduler(object):
	"""Threaded scheduler that allows for updates mid-execution unlike http://docs.python.org/library/sched.html#module-sched"""
	def __init__(self):
		self.addq = queue.Queue()
		self.schedule = []
		self.thread = None
		self.run = True
	
	def process(self, threaded=True):
		if threaded:
			self.thread = threading.Thread(name='shedulerprocess', target=self._process)
			self.thread.start()
		else:
			self._process()

	def _process(self):
		while self.run:
			wait = 5
			updated = False
			if self.schedule:
				wait = self.schedule[0].next - time.time()
			try:
				newtask = self.addq.get(True, wait)
			except queue.Empty:
				cleanup = []
				for task in self.schedule:
					if time.time() >= task.next:
						updated = True
						if not task.run():
							cleanup.append(task)
					else:
						break
				for task in cleanup:
					x = self.schedule.pop(self.schedule.index(task))
			else:
				updated = True
				self.schedule.append(newtask)
			finally:
				if updated: self.schedule = sorted(self.schedule, key=lambda task: task.next)
				print [x.name for x in self.schedule]

	def add(self, name, seconds, callback, args=None, kwargs=None, repeat=False, qpointer=None):
		self.addq.put(Task(name, seconds, callback, args, kwargs, repeat, qpointer))
	
	def quit(self):
		self.run = False
