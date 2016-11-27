#alexa/thread_manager.py

import threading
from alexa import logger

log = logger.getLogger(__name__)

class ThreadManager:

	class _Worker(threading.Thread):
		def __init__(self, *args):
			self._args = args
			threading.Thread.__init__(self)

		def run(self):
			try:
				if len(self._args) == 0:
					self.worker()
				else:
					self.worker(*self._args)

			except Exception:
				log.exception("message")


	def __init__(self):
		self.threads = []

	def start(self, target, stop, *args):
		if not target or not stop:
			raise NotImplementedError("Please provide the 'target' and/or 'stop' arg(s)")

		t = self._Worker(*args)
		t.worker = target
		t.thread_stopper = stop
		self.threads.append(t)
		t.start()

	def stop_all(self):
		#TODO: run periodic clean up of self.threads
		for t in self.threads:
			if t.isAlive():
				t.thread_stopper()

thread_manager = ThreadManager()
