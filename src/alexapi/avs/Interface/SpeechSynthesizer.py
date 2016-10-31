#alexapi/avs/Interface/SpeechSynthesizer.py

import json
import uuid
import threading

import alexapi.shared as shared
import alexapi.player.player as player
import alexapi.player.player_state as pstate

class SpeechSynthesizer:
	__avsi = None
	__token = None


	def __init__(self, avs_interface):
		self.__avsi = avs_interface

	def __playerCallback(self, state):
		if state == 3:
			self.SpeechStarted()

		elif state == 6:
			self.SpeechFinished()

	def Speak(self, payload):
		self.__token = payload.json['directive']['payload']['token']

		filename = "file://" + payload.filename
		player.play_avr(filename, self.__playerCallback)

	def SpeechStarted(self):
		j = {
			"event": {
				"header": {
					"namespace": "SpeechSynthesizer",
					"name": "SpeechStarted",
					"messageId": "message-ddid-123",
				},
				"payload": {
					"token": ""
				}
			}
		}

		data = json.loads(json.dumps(j))
		data['event']['payload']['token'] = self.__token
		data['event']['header']['messageId'] = str(uuid.uuid4())

		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])
		response = self.__avsi.get_avs_session().post(path, payload)
		return response

	def SpeechFinished(self):
		j = {
			"event": {
				"header": {
					"namespace": "SpeechSynthesizer",
					"name": "SpeechFinished",
					"messageId": "",
				},
				"payload": {
					"token": ""
				}
			}
		}

		data = json.loads(json.dumps(j))
		data['event']['payload']['token'] = self.__token
		data['event']['header']['messageId'] = str(uuid.uuid4())
		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])
		response = self.__avsi.get_avs_session().post(path, payload)

		return response
