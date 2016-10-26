#alexapi/AVS/interface_manager.py

import alexapi.shared as shared
from speech_recognizer import *

class Interface:
	__directive_path = None
	__avs_session = None

	def __init__(self, avs_session):
		self.__avs_session = avs_session

	def __get(self, argument):
		"""Dispatch method"""
		# prefix the method_name with 'number_' because method names
		# cannot begin with an integer.
		method_name = 'api_event_' + str(argument)

		# Get the method from 'self'. Default to a lambda.
		method = getattr(self, method_name, lambda: "nothing")

		# Call the method as we return it
		return method()

	def get_avs_session(self):
		return self.__avs_session

	def process_event(self, API):
		print "Processing event: %s" % API
		return self.__get(API)

	def __check_if_not_error(self, response):
		if not response.status_code >= 200 and not response.status_code < 300:
			print("{}(process_response Error){} Status Code: {} - {}".format(shared.bcolors.WARNING, shared.bcolors.ENDC, response.status_code, response.text))
			return False

		return True

	# Call API
	def api_event_SpeechRecognizer(self):
		api = SpeechRecognizer(self)
		response = api.send()
		if self.__check_if_not_error(response):
			api.process(response)