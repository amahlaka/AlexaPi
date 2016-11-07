#alexapi/avs/Interface/SpeechSynthesizer.py

import json
import uuid
import threading

import alexa.helper.shared as shared
from alexa.player.player import player

class SpeechSynthesizer:
	_avsi = None
	_token = None


	def __init__(self, avs_interface):
		self._avsi = avs_interface

	def _playerCallback(self, state):
		print 'STATE: ' + str(state)

		if state == 3:
			self.SpeechStarted()

		elif state == 6:
			self.SpeechFinished()

	def Speak(self, payload):
		self._token = payload.json['directive']['payload']['token']
		content = "file://" + payload.filename
		player.package.add(token=self._token, content=content)
		player.play_avs_response(self._token, self._playerCallback)

		#player.pstate.add_mediaInfo(nav_token=nav_token, offset=offset, streamFormat=streamFormat, url=url, play_behavior=play_behavior, content=content)
		#pThread = threading.Thread(target=player.play_media, args=(nav_token, self.__playerCallback, )) #TODO: Is nav_token unique
		#pThread.start()

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
		data['event']['payload']['token'] = self._token
		data['event']['header']['messageId'] = str(uuid.uuid4())

		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])
		response = self._avsi.get_avs_session().post(path, payload)
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
		data['event']['payload']['token'] = self._token
		data['event']['header']['messageId'] = str(uuid.uuid4())
		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])
		response = self._avsi.get_avs_session().post(path, payload)

		return response
