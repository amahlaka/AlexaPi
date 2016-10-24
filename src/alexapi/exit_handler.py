import sys
import signal
import shutil

import shared as shared

class CleanUp:
	__session = False
	__executed = False

	def __init__(self, session=False):
		if session:
			self.__session = session

		for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
			signal.signal(sig, self.cleanup)

	def add_session_cleanup(self, session):
		self.__session = session

	def cleanup(self, signal=False, frame=False):
		if not self.__executed:
			print "Exiting..."

			shutil.rmtree(shared.tmp_path)

			if self.__session:
				print "Closing session..."
				self.__session.close()

			self.__executed = True

		sys.exit(0)
