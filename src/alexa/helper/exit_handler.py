import sys
import signal
import shutil

import alexa.helper.shared as shared
from alexa.helper.thread import thread_manager

class CleanUp:
	__session = False
	__executed = False

	def __init__(self):
		for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
			signal.signal(sig, self.cleanup)

	def cleanup(self, signal=False, frame=False):
		if not self.__executed:
			print "Exiting..."
			thread_manager.stop_all()
			shutil.rmtree(shared.tmp_path)
			self.__executed = True

		sys.exit(0)
