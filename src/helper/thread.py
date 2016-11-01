import os
import sys
import time
import threading

class ThreadManager:
	__threads = []

	class __Worker(threading.Thread):
		def __init__(self):
			threading.Thread.__init__(self)

		def run(self):
			self.work()

		def stop(self):
			raise NotImplementedError("Please Implement this method")

		def work(self, kill_received):
			raise NotImplementedError("Please Implement this method")

	def __init__(self):
		pass

	def start(self, work, stop):
		if not work or not stop:
			raise NotImplementedError("Please Implement the 'work' and/or 'stop' method(s)")

		t = self.__Worker()
		t.work = work
		t.stop = stop
		self.__threads.append(t)
		t.start()

	def stop_all(self):
		for t in self.__threads:
			t.stop()

thread_manager = ThreadManager()
