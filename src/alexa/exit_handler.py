#alexa/exit_handler.py

import sys
import signal
import shutil

import alexa.thread_manager

class CleanUp:

	def __init__(self, tmp_dir):
		self._tmp_dir = tmp_dir
		self.__executed = False

		for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
			signal.signal(sig, self.cleanup)

	def cleanup(self, signal=False, frame=False):
		if not self.__executed:
			print "\n\nExiting...\n"
			alexa.thread_manager.stop_all()
			shutil.rmtree(self._tmp_dir)
			self.__executed = True

		sys.exit(0)
