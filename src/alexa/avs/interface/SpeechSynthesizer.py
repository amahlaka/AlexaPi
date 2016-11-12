#alexa/avs/interface/SpeechSynthesizer.py

import json
import uuid

from alexa import alexa

class SpeechSynthesizer:

	def __init__(self, avs_interface):
		self._interface_manager = avs_interface
		self._token = None

	def _playerCallback(self, state):
		if state == 3:
			self.SpeechStarted()

		elif state == 6:
			self.SpeechFinished()

	def initialState(self):
		return {
			"header":{
				"name":"SpeechState",
				"namespace":"SpeechSynthesizer"
			},
				"payload":{
				"offsetInMilliseconds":0,
				"playerActivity":"FINISHED",
				"token":""
			}
		}

	def Speak(self, payload):
		self._token = payload.json['directive']['payload']['token']
		content = "file://" + payload.filename
		alexa.player.package.add(token=self._token, content=content)
		alexa.player.play_avs_response(self._token, self._playerCallback) #TODO: Is nav_token unique

	def SpeechStarted(self):
		speech_started = {
			"event": {
				"header": {
					"namespace": "SpeechSynthesizer",
					"name": "SpeechStarted",
					"messageId": "",
				},
				"payload": {
					"token": ""
				}
			}
		}

		msg_id = str(uuid.uuid4())
		data = json.loads(json.dumps(speech_started))
		data['event']['payload']['token'] = self._token
		data['event']['header']['messageId'] = msg_id

		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(alexa.config['alexa']['API_Version'], alexa.config['alexa']['EventPath'])

		return self._interface_manager.send_event(msg_id, path, payload)

	def SpeechFinished(self):
		speech_finished = {
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

		msg_id = str(uuid.uuid4())
		data = json.loads(json.dumps(speech_finished))
		data['event']['payload']['token'] = self._token
		data['event']['header']['messageId'] = msg_id
		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(alexa.config['alexa']['API_Version'], alexa.config['alexa']['EventPath'])

		return self._interface_manager.send_event(msg_id, path, payload)
