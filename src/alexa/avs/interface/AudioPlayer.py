#alexapi/AVS/Interface/AudioPlayer.py

import json
import uuid
import threading

import alexa.helper.shared as shared
from alexa.player.player import player

class AudioPlayer:
	__avsi = None
	__token = None


	def __init__(self, avs_interface):
		self.__avsi = avs_interface

	def _playerCallback(self, state):
		print 'STATE: ' + str(state)

		if state == 3:
			self.PlaybackStarted()

		elif state == 6:
			self.PlaybackFinished()

		elif state == 8:
			self.PlaybackNearlyFinished()

	def ClearQueue(self, payload):
		#https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/audioplayer#clearqueue
		#TODO: Not implemented yet
		clear_type = payload.json['directive']['payload']['clearBehavior']
		pThread = threading.Thread(target=player.clear_queue_media_player, args=(clear_type, ))
		pThread.start()

	def Stop(self, payload):
		pThread = threading.Thread(target=player.stop_media_player)
		pThread.start()

	def Play(self, payload):
		#https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/audioplayer#play
		play_behavior		= payload.json['directive']['payload']['playBehavior']
		nav_token		= payload.json['directive']['payload']['audioItem']['stream']['token']
		url			= payload.json['directive']['payload']['audioItem']['stream']['url']
		offset			= payload.json['directive']['payload']['audioItem']['stream']['offsetInMilliseconds']

		if 'progressReportIntervalInMilliseconds' in payload.json['directive']['payload']:
			progressReport = payload.json['directive']['payload']['progressReportIntervalInMilliseconds']

		if 'streamFormat' in payload.json['directive']['payload']['audioItem']['stream']:
			streamFormat = payload.json['directive']['payload']['audioItem']['stream']['streamFormat']
		else:
			streamFormat = False

		if url.startswith("cid:"):
			content = "file://" + payload.filename
		else:
			content = url

		player.package.add(token=nav_token, offset=offset, streamFormat=streamFormat, url=url, play_behavior=play_behavior, content=content)
		pThread = threading.Thread(target=player.play_avs_response, args=(nav_token, self._playerCallback, )) #TODO: Is nav_token unique
		pThread.start()

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
		data['event']['header']['messageId'] = str(uuid.uuid4())
		data['event']['payload']['token'] = player.getCurrentToken()
		data['event']['payload']['offsetInMilliseconds'] = 0 #TODO: send audio current offset in milliseconds

		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])
		response = self.__avsi.get_avs_session().post(path, payload)
		self.__avsi.process_response(response)

	def PlaybackNearlyFinished(self):
		j ={
			"event": {
				"header": {
					"namespace": "AudioPlayer",
					"name": "PlaybackNearlyFinished",
					"messageId": "{{STRING}}"
				},
				"payload": {
					"token": "{{STRING}}",
					"offsetInMilliseconds": "{{LONG}}"
				}
			}
		}

		data = json.loads(json.dumps(j))
		data['event']['header']['messageId'] = str(uuid.uuid4())
		data['event']['payload']['token'] = player.getCurrentToken()
		data['event']['payload']['offsetInMilliseconds'] = 0 #TODO: send audio current offset in milliseconds
		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])
		response = self.__avsi.get_avs_session().post(path, payload)
		self.__avsi.process_response(response)

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
		data['event']['header']['messageId'] = str(uuid.uuid4())
		data['event']['payload']['token'] = player.pstate.currentItem
		data['event']['payload']['offsetInMilliseconds'] = 0 #TODO: send audio current offset in milliseconds
		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])
		response = self.__avsi.get_avs_session().post(path, payload)
		self.__avsi.process_response(response)
