#alexapi/AVS/Interface/AudioPlayer.py

import json
import uuid
import threading

import alexapi.shared as shared
import alexapi.player.player as player

class AudioPlayer:
	__avsi = None
	__token = None


	def __init__(self, avs_interface):
		self.__avsi = avs_interface

	def __playerCallback(self, state):
		if state == 3:
			self.SpeechStarted()

		elif state == 6:
			self.SpeechFinished()

	def ClearQueue(self, payload):
		#https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/audioplayer#clearqueue
		#TODO: Not implemented yet
		clear_type = payload.json['directive']['payload']['clearBehavior']
		#pThread = threading.Thread(target=player.play_avr, args=(filename, self.__playerCallback, ))
		#pThread.start()

	def Stop(self, payload):
		pThread = threading.Thread(target=player.stop_media_player)
		pThread.start()

	def Play(self, payload):
		#https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/audioplayer#play
		play_behavior = payload.json['directive']['payload']['playBehavior']
		url           = payload.json['directive']['payload']['audioItem']['stream']['url']
		nav_token     = payload.json['directive']['payload']['audioItem']['stream']['token']
		streamFormat  = payload.json['directive']['payload']['audioItem']['stream']['streamFormat']
		offset        = payload.json['directive']['payload']['audioItem']['stream']['offsetInMilliseconds']

		if url.startswith("cid:"):
			content = "file://" + payload.filename
		else:
			content = stream['streamUrl']

		pThread = threading.Thread(target=player.play_media, args=(content, offset))
		pThread.start()
		#pThread = threading.Thread(target=player.play_avr, args=(filename, self.__playerCallback, ))

	def PlaybackStarted(self):
		j = {
			"event": {
				"header": {
					"namespace": "AudioPlayer",
					"name": "PlaybackStarted",
					"messageId": "message-ddid-123",
				},
				"payload": {
					"token": "",
					"offsetInMilliseconds": "{{LONG}}"
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

	def PlaybackFinished(self):
		j = {
			"event": {
				"header": {
					"namespace": "AudioPlayer",
					"name": "PlaybackFinished",
					"messageId": "",
				},
				"payload": {
					"token": "",
					"offsetInMilliseconds": "{{LONG}}"
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
