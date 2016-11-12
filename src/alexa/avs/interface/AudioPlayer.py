#alexapi/AVS/Interface/AudioPlayer.py

import json
import uuid

import alexa.helper.shared as shared

class AudioPlayer:

	def __init__(self, avs_interface):
		self._interface_manager = avs_interface
		self._token = None

	def _playerCallback(self, state):
		if state == 3:
			self.PlaybackStarted()

		elif state == 6:
			self.PlaybackFinished()

		elif state == 8:
			self.PlaybackNearlyFinished()

	def initialState(self):
		return {
			"header":{
				"name":"PlaybackState",
				"namespace":"AudioPlayer"
			},
			"payload":{
				"offsetInMilliseconds":0,
				"playerActivity":"IDLE",
				"token":"{{STRING}}"
			}
		}

	def ClearQueue(self, payload): #https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/audioplayer#clearqueue
		#TODO: Not implemented yet
		clear_type = payload.json['directive']['payload']['clearBehavior']
		shared.player.clear_queue(clear_type)

	def Stop(self, payload):
		shared.player.stop()

	def Play(self, payload): #https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/audioplayer#play
		skip = False
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
			if not payload.filename:
				skip = True
			else:
				content = "file://" + payload.filename
		else:
			content = url

		if not skip:
			shared.player.package.add(token=nav_token, offset=offset, streamFormat=streamFormat, url=url, play_behavior=play_behavior, content=content)
			shared.player.play_avs_response(nav_token, self._playerCallback) #TODO: Is nav_token unique
		else:
			print 'Skipping...' #TODO: Is this normal? Find out why we get here

	def PlaybackStarted(self):
		playback_started = {
			"event": {
				"header": {
					"namespace": "AudioPlayer",
					"name": "PlaybackStarted",
					"messageId": "{{STRING}}",
				},
				"payload": {
					"token": "",
					"offsetInMilliseconds": "{{LONG}}"
				}
			}
		}

		msg_id = str(uuid.uuid4())
		data = json.loads(json.dumps(playback_started))
		data['event']['header']['messageId'] = msg_id
		data['event']['payload']['token'] = shared.player.getCurrentToken()
		data['event']['payload']['offsetInMilliseconds'] = 0 #TODO: send audio current offset in milliseconds
		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])

		return self._interface_manager.send_event(msg_id, path, payload)

	def PlaybackNearlyFinished(self):
		playback_nearly_finished ={
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

		msg_id = str(uuid.uuid4())
		data = json.loads(json.dumps(playback_nearly_finished))
		data['event']['header']['messageId'] = msg_id
		data['event']['payload']['token'] = shared.player.getCurrentToken()
		data['event']['payload']['offsetInMilliseconds'] = 0 #TODO: send audio current offset in milliseconds
		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])

		return self._interface_manager.send_event(msg_id, path, payload)

	def PlaybackFinished(self):
		playback_finished = {
			"event": {
				"header": {
					"namespace": "AudioPlayer",
					"name": "PlaybackFinished",
					"messageId": "{{STRING}}",
				},
				"payload": {
					"token": "",
					"offsetInMilliseconds": "{{LONG}}"
				}
			}
		}

		msg_id = str(uuid.uuid4())
		data = json.loads(json.dumps(playback_finished))
		data['event']['header']['messageId'] = msg_id
		data['event']['payload']['token'] = shared.player.getCurrentToken()
		data['event']['payload']['offsetInMilliseconds'] = 0 #TODO: send audio current offset in milliseconds
		payload = [
			('file', ('request', json.dumps(data), 'application/json; charset=UTF-8')),
		]
		path = '/{}{}'.format(shared.config['alexa']['API_Version'], shared.config['alexa']['EventPath'])

		return self._interface_manager.send_event(msg_id, path, payload)
