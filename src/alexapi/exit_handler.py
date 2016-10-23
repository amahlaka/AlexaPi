import sys
import signal
import shutil


class CleanUp:
	__tmp_path = False
	__session = False

	def __init__(self, path, session):
		self.__tmp_path = path
		self.__session = session

		for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
			signal.signal(sig, self.__cleanup)

	def __cleanup(self, signal, frame):
		print "Exiting..."
		if self.__tmp_path:
			shutil.rmtree(self.__tmp_path)

		if self.__session:
			self.__session.close()

		sys.exit(0)
