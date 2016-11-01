#alexapi/avs/directive_dispatcher.py

import json
import email

import alexapi.shared as shared
import alexapi.player.player as player
import alexapi.player.tunein as tunein

tunein_parser = tunein.TuneIn(5000)

class DirectiveDispatcher:
	__interface_manager = None
	__payload = None

	def __init__(self, interface_manager):
		self.__interface_manager = interface_manager
		self.__payload =  interface_manager.Payload

	def find_attachement(self, payload, directive):
		def get_attachement(url):
			for msg in payload:
				if msg.get_content_type() == "application/octet-stream":
					content_id = msg.get('Content-ID').strip("<>")
					if content_id == url.lstrip('cid:'):
						return msg

		if "format" in directive['directive']['payload'] and directive['directive']['payload']['format'] == 'AUDIO_MPEG':
			return get_attachement(directive['directive']['payload'] and directive['directive']['payload']['url'])

		elif "streamFormat" in directive['directive']['payload']['audioItem']['stream'] and directive['directive']['payload']['audioItem']['stream']['streamFormat'] == 'AUDIO_MPEG':
			return get_attachement(directive['directive']['payload']['audioItem']['stream']['url'])

		return False

	def alexa_getnextitem(nav_token):
		# https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/audioplayer-getnextitem-request
		time.sleep(0.5)
		if not player.is_avr_playing():
			if shared.debug: print("{}Sending GetNextItem Request...{}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC))
			url = 'https://access-alexa-na.amazon.com/v1/avs/audioplayer/getNextItem'
			headers = {'Authorization' : 'Bearer %s' % gettoken(), 'content-type' : 'application/json; charset=UTF-8'}
			d = {
				"messageHeader": {},
				"messageBody": {
					"navigationToken": nav_token
				}
			}
			r = requests.post(url, headers=headers, data=json.dumps(d))
			process_response(r)

	def alexa_playback_progress_report_request(requestType, playerActivity, streamid):
		# https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/audioplayer-events-requests
		# streamId                  Specifies the identifier for the current stream.
		# offsetInMilliseconds      Specifies the current position in the track, in milliseconds.
		# playerActivity            IDLE, PAUSED, or PLAYING
		if shared.debug: print("{}Sending Playback Progress Report Request...{}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC))
		headers = {'Authorization' : 'Bearer %s' % gettoken()}
		d = {
			"messageHeader": {},
			"messageBody": {
				"playbackState": {
					"streamId": streamid,
					"offsetInMilliseconds": 0,
					"playerActivity": playerActivity.upper()
				}
			}
		}

		if requestType.upper() == "ERROR":
			# The Playback Error method sends a notification to AVS that the audio player has experienced an issue during playback.
			url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackError"
		elif requestType.upper() ==  "FINISHED":
			# The Playback Finished method sends a notification to AVS that the audio player has completed playback.
			url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackFinished"
		elif requestType.upper() ==  "IDLE":
			# The Playback Idle method sends a notification to AVS that the audio player has reached the end of the playlist.
			url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackIdle"
		elif requestType.upper() ==  "INTERRUPTED":
			# The Playback Interrupted method sends a notification to AVS that the audio player has been interrupted.
			# Note: The audio player may have been interrupted by a previous stop Directive.
			url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackInterrupted"
		elif requestType.upper() ==  "PROGRESS_REPORT":
			# The Playback Progress Report method sends a notification to AVS with the current state of the audio player.
			url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackProgressReport"
		elif requestType.upper() ==  "STARTED":
			# The Playback Started method sends a notification to AVS that the audio player has started playing.
			url = "https://access-alexa-na.amazon.com/v1/avs/audioplayer/playbackStarted"

		r = requests.post(url, headers=headers, data=json.dumps(d))
		if r.status_code != 204:
			print("{}(alexa_playback_progress_report_request Response){} {}".format(shared.bcolors.WARNING, shared.bcolors.ENDC, r))
		else:
			if shared.debug: print("{}Playback Progress Report was {}Successful!{}".format(shared.bcolors.OKBLUE, shared.bcolors.OKGREEN, shared.bcolors.ENDC))

	def tuneinplaylist(url):
		global tunein_parser
		if shared.debug: print("TUNE IN URL = {}".format(url))
		req = requests.get(url)
		lines = req.content.split('\n')

		nurl = tunein_parser.parse_stream_url(lines[0])
		if (len(nurl) != 0):
			return nurl[0]

		return ""

	def processor(self, r):
		print("{}Processing Request Response...{}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC))

		if r and r.status_code == 200:
			data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
			msg = email.message_from_string(data)

			for payload in msg.get_payload():
				if payload.get_content_type() == "application/json":
					j = json.loads(payload.get_payload())
					if shared.debug: print("\n{}JSON String Returned:{} {}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC, json.dumps(j)))

					binary = self.find_attachement(msg.get_payload(), j)
					if binary:
						filename = shared.tmp_path + binary.get('Content-ID').strip("<>")+".mp3"
						with open(filename, 'wb') as f:
							print
							print 'Saving payload: %s' % filename
							print
							f.write(binary.get_payload())
					else:
						filename = False

					self.__payload.json = j
					self.__payload.filename = filename
					self.__interface_manager.dispatch_directive(self.__payload)

			#continue

			return
			'''
					# Now process the response
					if 'directive' in j:
						directive = j['directive']['header']['namespace']


						if len(j['directive']) == 0:
							print("0 Directives received")
							shared.led.rec_off()
							shared.led.status_off()

						if directive == 'SpeechSynthesizer':
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
		'''

		elif r and r.status_code == 204:
			shared.led.rec_off()
			shared.led.blink_error()
			if shared.debug: print("{}Request Response is null {}(This is OKAY!){}".format(shared.bcolors.OKBLUE, shared.bcolors.OKGREEN, shared.bcolors.ENDC))

		else:
			player.play_avr(shared.resources_path+'error.mp3', 0)
			if r:
				print("{}(process_response Error){} Status Code: {} - {}".format(shared.bcolors.WARNING, shared.bcolors.ENDC, r.status_code, r.text))
				#r.close()

			shared.led.status_off()
			shared.led.blink_valid_data_received()
