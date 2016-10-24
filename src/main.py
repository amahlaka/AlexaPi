#! /usr/bin/env python

import re
import os
import cgi
import sys
import time
import json
import wave
import email
import getch
import tunein
import random
import datetime
import requests
import alsaaudio
import threading
import fileinput
import webrtcvad
import traceback

from pocketsphinx import get_model_path
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *

import alexapi.exit_handler as exit_handler
import alexapi.avs as avs
import alexapi.player as player
import alexapi.player_state as pstate
import alexapi.shared as shared

#Setup
recorded = False
path = os.path.realpath(__file__).rstrip(os.path.basename(__file__))
resources_path = os.path.join(path, 'resources', '')

# PocketSphinx configuration
ps_config = Decoder.default_config()

# Set recognition model to US
ps_config.set_string('-hmm', os.path.join(get_model_path(), 'en-us'))
ps_config.set_string('-dict', os.path.join(get_model_path(), 'cmudict-en-us.dict'))

#Specify recognition key phrase
ps_config.set_string('-keyphrase', shared.config['sphinx']['trigger_phrase'])
ps_config.set_float('-kws_threshold',1e-5)

# Hide the VERY verbose logging information
ps_config.set_string('-logfn', '/dev/null')

# Process audio chunk by chunk. On keyword detected perform action and restart search
decoder = Decoder(ps_config)

#Variables
button_pressed = False
start = time.time()
tunein_parser = tunein.TuneIn(5000)
vad = webrtcvad.Vad(2)
http = False
exit = False

# constants
VAD_SAMPLERATE = 16000
VAD_FRAME_MS = 30
VAD_PERIOD = (VAD_SAMPLERATE / 1000) * VAD_FRAME_MS
VAD_SILENCE_TIMEOUT = 1000
VAD_THROWAWAY_FRAMES = 10
MAX_RECORDING_LENGTH = 8
MAX_VOLUME = 100
MIN_VOLUME = 30


def alexa_speech_recognizer():
	# https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/speechrecognizer-requests
	if shared.debug: print("{}Sending Speech Request...{}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC))
	r = http.send_event(avs.API.SpeechRecognizer)

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

def process_response(r):
	if shared.debug: print("{}Processing Request Response...{}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC))
	pstate.nav_token = ""
	pstate.streamurl = ""
	pstate.streamid = ""
	if r.status_code == 200:
		data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
		msg = email.message_from_string(data)
		for payload in msg.get_payload():
			if payload.get_content_type() == "application/json":
				j =  json.loads(payload.get_payload())
				if shared.debug: print("{}JSON String Returned:{} {}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC, json.dumps(j)))
			elif payload.get_content_type() == "audio/mpeg":
				filename = shared.tmp_path + payload.get('Content-ID').strip("<>")+".mp3"
				with open(filename, 'wb') as f:
					f.write(payload.get_payload())
			else:
				if shared.debug: print("{}NEW CONTENT TYPE RETURNED: {} {}".format(shared.bcolors.WARNING, shared.bcolors.ENDC, payload.get_content_type()))
		# Now process the response
		if 'directives' in j['messageBody']:
			if len(j['messageBody']['directives']) == 0:
				if shared.debug: print("0 Directives received")
				shared.led.rec_off()
				shared.led.status_off()

			for directive in j['messageBody']['directives']:
				if directive['namespace'] == 'SpeechSynthesizer':
					if directive['name'] == 'speak':
						shared.led.rec_off()
						player.play_avr("file://" + shared.tmp_path + directive['payload']['audioContent'].lstrip("cid:")+".mp3")
					for directive in j['messageBody']['directives']: # if Alexa expects a response
						if directive['namespace'] == 'SpeechRecognizer': # this is included in the same string as above if a response was expected
							if directive['name'] == 'listen':
								if shared.debug: print("{}Further Input Expected, timeout in: {} {}ms".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC, directive['payload']['timeoutIntervalInMillis']))
								player.play_avr(resources_path+'beep.wav', 0, 100)
								timeout = directive['payload']['timeoutIntervalInMillis']/116
								# listen until the timeout from Alexa
								silence_listener(timeout)
								# now process the response
								alexa_speech_recognizer()
				elif directive['namespace'] == 'AudioPlayer':
					#do audio stuff - still need to honor the playBehavior
					if directive['name'] == 'play':
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
				elif directive['namespace'] == "Speaker":
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
		led.blink_valid_data_received()
		player.resume_media_player()
		if shared.debug: print("{}Request Response is null {}(This is OKAY!){}".format(shared.bcolors.OKBLUE, shared.bcolors.OKGREEN, shared.bcolors.ENDC))
	else:
		print("{}(process_response Error){} Status Code: {} - {}".format(shared.bcolors.WARNING, shared.bcolors.ENDC, r.status_code, r.text))
		r.close()
		led.blink_error()

def tuneinplaylist(url):
	global tunein_parser
	if shared.debug: print("TUNE IN URL = {}".format(url))
	req = requests.get(url)
	lines = req.content.split('\n')

	nurl = tunein_parser.parse_stream_url(lines[0])
	if (len(nurl) != 0):
		return nurl[0]

	return ""


def detect_button(channel):
        global button_pressed
        buttonPress = time.time()
        button_pressed = True
        if shared.debug: print("{}Button Pressed! Recording...{}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC))
        time.sleep(.5) # time for the button input to settle down
        while (shared.get_button_status() == 0):
                button_pressed = True
                time.sleep(.1)
                if time.time() - buttonPress > 10: # pressing button for 10 seconds triggers a system halt
			player.play_avr(resources_path+'alexahalt.mp3')
			if shared.debug: print("{} -- 10 second putton press.  Shutting down. -- {}".format(shared.bcolors.WARNING, shared.bcolors.ENDC))
			os.system("halt")
        if shared.debug: print("{}Recording Finished.{}".format(shared.bcolors.OKBLUE, shared.bcolors.ENDC))
        button_pressed = False
        time.sleep(.5) # more time for the button to settle down

def silence_listener(throwaway_frames):
		global button_pressed
		# Reenable reading microphone raw data
		inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, shared.config['sound']['device'])
		inp.setchannels(1)
		inp.setrate(VAD_SAMPLERATE)
		inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
		inp.setperiodsize(VAD_PERIOD)
		audio = ""


		# Buffer as long as we haven't heard enough silence or the total size is within max size
		thresholdSilenceMet = False
		frames = 0
		numSilenceRuns = 0
		silenceRun = 0
		start = time.time()

		# do not count first 10 frames when doing VAD
		while (frames < throwaway_frames): # VAD_THROWAWAY_FRAMES):
			l, data = inp.read()
			frames = frames + 1
			if l:
				audio += data
				isSpeech = vad.is_speech(data, VAD_SAMPLERATE)

		# now do VAD
		while button_pressed == True or ((thresholdSilenceMet == False) and ((time.time() - start) < MAX_RECORDING_LENGTH)):
			l, data = inp.read()
			if l:
				audio += data

				if (l == VAD_PERIOD):
					isSpeech = vad.is_speech(data, VAD_SAMPLERATE)

					if (isSpeech == False):
						silenceRun = silenceRun + 1
						#print "0"
					else:
						silenceRun = 0
						numSilenceRuns = numSilenceRuns + 1
						#print "1"

			# only count silence runs after the first one
			# (allow user to speak for total of max recording length if they haven't said anything yet)
			if (numSilenceRuns != 0) and ((silenceRun * VAD_FRAME_MS) > VAD_SILENCE_TIMEOUT):
				thresholdSilenceMet = True
			shared.led.rec_on()

		if shared.debug: print ("Debug: End recording")

		# if shared.debug: player.play_avr(resources_path+'beep.wav', 0, 100)

		shared.led.rec_off()
		rf = open(shared.tmp_path + 'recording.wav', 'w')
		rf.write(audio)
		rf.close()
		inp.close()


def start():
	global vad, button_pressed
	shared.Button(detect_button)

	while True:
		record_audio = False

		# Enable reading microphone raw data
		inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, shared.config['sound']['device'])
		inp.setchannels(1)
		inp.setrate(16000)
		inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
		inp.setperiodsize(1024)
		start = time.time()

		decoder.start_utt()

                while record_audio == False:

			time.sleep(.1)

			# Process microphone audio via PocketSphinx, listening for trigger word
			while decoder.hyp() == None and button_pressed == False:
				# Read from microphone
				l,buf = inp.read()
				# Detect if keyword/trigger word was said
				decoder.process_raw(buf, False, False)

			# if trigger word was said
			if decoder.hyp() != None:
				if player.is_avr_playing():
					player.stop_avr()
					time.sleep(.5) #add delay before audio prompt

				if player.is_media_playing():
					player.stop_media_player()
					time.sleep(.5) #add delay before audio prompt

				start = time.time()
				record_audio = True
				player.play_avr(resources_path+'alexayes.mp3', 0)
			elif button_pressed:
				if player.is_avr_playing or player.is_media_playing(): player.stop_media_player()
				record_audio = True

		# do the following things if either the button has been pressed or the trigger word has been said
		if shared.debug: print ("detected the edge, setting up audio")

		# To avoid overflows close the microphone connection
		inp.close()

		# clean up the temp directory
		if shared.debug == False:
			for file in os.listdir(shared.tmp_path):
				file_path = os.path.join(shared.tmp_path, file)
				try:
					if os.path.isfile(file_path):
						os.remove(file_path)
				except Exception as e:
					print(e)

		if shared.debug: print "Starting to listen..."
		silence_listener(VAD_THROWAWAY_FRAMES)

		if shared.debug: print "Debug: Sending audio to be processed"
		alexa_speech_recognizer()

		# Now that request is handled restart audio decoding
		decoder.end_utt()

def setup():
	global http, exit
	exit = exit_handler.CleanUp()

	http = avs.Http()
	exit.add_session_cleanup(http)
	player.setup(alexa_playback_progress_report_request, alexa_getnextitem, tuneinplaylist)

	if (shared.silent == False): player.play_avr(resources_path+"hello.mp3")

if __name__ == "__main__":
	try:
		setup()
		start()

	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
		print ''.join('!! ' + line for line in lines)  # Log it or whatever here

	finally:
		exit.cleanup()
