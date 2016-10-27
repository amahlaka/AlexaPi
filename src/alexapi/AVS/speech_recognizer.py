#alexapi/AVS/speech_recognizer.py

import json

import alexapi.shared as shared
import alexapi.player_state as pstate

class API:
	SpeechRecognizer = 'SpeechRecognizer'


#TODO: Make Abstract
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

	def send(self):
		with open('{}recording.wav'.format(shared.tmp_path)) as wav_file:
			payload = [
				('file', ('request', json.dumps(self.__api), 'application/json; charset=UTF-8')),
				('file', ('audio', wav_file, 'application/octet-stream'))
			]
			path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])
			response = self.__avsi.get_avs_session().post(path, payload)

		return response

	def process(self, r):
		print("{}Processing Request Response...{}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC))
