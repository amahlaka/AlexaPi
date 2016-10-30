#alexapi/AVS/Interface/SpeechRecognizer.py

import json

import alexapi.shared as shared

class SpeechRecognizer:
	__avsi = None
	__api = {
		"event": {
			"header": {
				"namespace": "SpeechRecognizer",
				"name": "Recognize",
				"messageId": "message-id-123",
				"dialogRequestId": "dialog-request-123"
			},
			"payload": {
				"profile": "CLOSE_TALK",
				"format": "AUDIO_L16_RATE_16000_CHANNELS_1"
			}
		}
	}

	def __init__(self, avs_interface):
		self.__avsi = avs_interface

	def Recognize(self):
		with open('{}recording.wav'.format(shared.tmp_path)) as wav_file:
			payload = [
				('file', ('request', json.dumps(self.__api), 'application/json; charset=UTF-8')),
				('file', ('audio', wav_file, 'application/octet-stream'))
			]
			path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])
			response = self.__avsi.get_avs_session().post(path, payload)

		return response

	def process(self):
		print("{}Processing Request Response...{}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC))
