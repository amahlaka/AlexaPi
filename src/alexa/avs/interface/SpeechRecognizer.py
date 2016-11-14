#alexa/avs/interface/SpeechRecognizer.py

import json
import uuid

import alexa

class SpeechRecognizer:

	def __init__(self, avs_interface):
		self._interface_manager = avs_interface

	def initialState(self):
		return False

	def Recognize(self):
		speech_recognizer_event = {
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

		with open('{}recording.wav'.format(alexa.tmp_path)) as wav_file:
			msg_id = str(uuid.uuid4())
			dialog_id = str(uuid.uuid4())
			event = json.loads(json.dumps(speech_recognizer_event))
			event['event']['header']['messageId'] = msg_id
			event['event']['header']['dialogRequestId'] = dialog_id
			payload = [
				('file', ('request', json.dumps(event), 'application/json; charset=UTF-8')),
				('file', ('audio', wav_file, 'application/octet-stream'))
			]
			path = '/{}{}'.format(alexa.config['alexa']['API_Version'], alexa.config['alexa']['EventPath'])

			return self._interface_manager.send_event(dialog_id, path, payload)
