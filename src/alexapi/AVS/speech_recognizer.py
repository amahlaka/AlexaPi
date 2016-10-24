#alexapi/AVS/speech_recognizer.py

import json
import email

import alexapi.shared as shared
import alexapi.player as player
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

		if r.status_code == 200:
			data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
			msg = email.message_from_string(data)

			#TODO: Fix when multiple directives
			for payload in msg.get_payload():
				if payload.get_content_type() == "application/json":
					j =  json.loads(payload.get_payload())
					if shared.debug: print("{}JSON String Returned:{} {}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC, json.dumps(j)))

				elif payload.get_content_type() == "application/octet-stream":
					filename = shared.tmp_path + payload.get('Content-ID').strip("<>")+".mp3"
					with open(filename, 'wb') as f:
						f.write(payload.get_payload())

				else:
					if shared.debug: print("{}NEW CONTENT TYPE RETURNED: {} {}".format(shared.bcolors.WARNING, shared.bcolors.ENDC, payload.get_content_type()))

			# Now process the response
			if 'directive' in j:
				directive = j['directive']['header']['namespace']

				if len(j['directive']) == 0:
					print("0 Directives received")
					shared.led.rec_off()
					shared.led.status_off()

				if directive == 'SpeechSynthesizer':
					print "Testing..."
					if j['directive']['header']['name'] == 'Speak':
						shared.led.rec_off()
						player.play_avr("file://" + shared.tmp_path + j['directive']['payload']['url'].lstrip("cid:")+".mp3")

				if directive == 'SpeechRecognizer': # this is included in the same string as above if a response was expected
					if j['directive']['header']['name'] == 'Listen':
						if shared.debug: print("{}Further Input Expected, timeout in: {} {}ms".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC, directive['payload']['timeoutIntervalInMillis']))
						player.play_avr(resources_path+'beep.wav', 0, 100)
						timeout = directive['payload']['timeoutIntervalInMillis']/116
						# listen until the timeout from Alexa
						silence_listener(timeout)
						# now process the response
						alexa_speech_recognizer()

				elif directive == 'AudioPlayer':
					#do audio stuff - still need to honor the playBehavior
					if j['directive']['header']['name'] == 'Play':
						pstate.nav_token = directive['payload']['navigationToken']
						for stream in directive['payload']['audioItem']['streams']:
							if stream['progressReportRequired']:
								pstate.streamid = stream['streamId']
								playBehavior = directive['payload']['playBehavior']
							if stream['streamUrl'].startswith("cid:"):
								content = "file://" + shared.tmp_path + stream['streamUrl'].lstrip("cid:")+".mp3"
							else:
								content = stream['streamUrl']
							pThread = threading.Thread(target=player.play_media, args=(content, stream['offsetInMilliseconds']))
							pThread.start()
					if directive['name'] == 'stop':
							pThread = threading.Thread(target=player.stop_media_player)
							pThread.start()
				elif directive == "Speaker":
					# speaker control such as volume
					if directive['name'] == 'SetVolume':
						vol_token = directive['payload']['volume']
						type_token = directive['payload']['adjustmentType']
						if (type_token == 'relative'):
							pstate.currVolume = pstate.currVolume + int(vol_token)
						else:
							pstate.currVolume = int(vol_token)

						if (pstate.currVolume > MAX_VOLUME):
							pstate.currVolume = MAX_VOLUME
						elif (pstate.currVolume < MIN_VOLUME):
							pstate.currVolume = MIN_VOLUME
						if shared.debug: print("new volume = {}".format(pstate.currVolume))

			elif 'audioItem' in j['messageBody']:		#Additional Audio Iten
				pstate.nav_token = j['messageBody']['navigationToken']
				for stream in j['messageBody']['audioItem']['streams']:
					if stream['progressReportRequired']:
						pstate.streamid = stream['streamId']
					if stream['streamUrl'].startswith("cid:"):
						content = "file://" + shared.tmp_path + stream['streamUrl'].lstrip("cid:")+".mp3"
					else:
						content = stream['streamUrl']
					pThread = threading.Thread(target=player.play_media, args=(content, stream['offsetInMilliseconds']))
					pThread.start()

			return

		elif r.status_code == 204:
			shared.led.rec_off()
			shared.led.blink_error()
			player.resume_media_player()
			if shared.debug: print("{}Request Response is null {}(This is OKAY!){}".format(shared.bcolors.OKBLUE, shared.bcolors.OKGREEN, shared.bcolors.ENDC))
		else:
			print("{}(process_response Error){} Status Code: {} - {}".format(shared.bcolors.WARNING, shared.bcolors.ENDC, r.status_code, r.text))
			r.close()
			shared.led.status_off()
			shared.led.blink_valid_data_received()
