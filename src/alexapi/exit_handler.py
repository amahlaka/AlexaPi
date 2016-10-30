import sys
import signal
import shutil

import shared as shared

class CleanUp:
	__session = False
	__executed = False

	def __init__(self):
		for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
			signal.signal(sig, self.cleanup)

	def cleanup(self, signal=False, frame=False):
		if not self.__executed:
			print "Exiting..."

			shutil.rmtree(shared.tmp_path)
			self.__executed = True

		sys.exit(0)
