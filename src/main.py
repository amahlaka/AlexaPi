#! /usr/bin/env python

import os
import tempfile
import signal
import shutil
import random
import time
import alsaaudio
import wave
import requests
import json
import re
import threading
import cgi
import email
import getch
import sys
import fileinput
import datetime
import tunein
import webrtcvad

from pocketsphinx import get_model_path
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *

import alexapi.session as session
import alexapi.player as player
import alexapi.player_state as pstate
from alexapi.shared import *

#Setup
recorded = False
path = os.path.realpath(__file__).rstrip(os.path.basename(__file__))
resources_path = os.path.join(path, 'resources', '')
tmp_path = os.path.join(tempfile.mkdtemp(prefix='AlexaPi-runtime-'), '')

# PocketSphinx configuration
ps_config = Decoder.default_config()

# Set recognition model to US
ps_config.set_string('-hmm', os.path.join(get_model_path(), 'en-us'))
ps_config.set_string('-dict', os.path.join(get_model_path(), 'cmudict-en-us.dict'))

#Specify recognition key phrase
ps_config.set_string('-keyphrase', config['sphinx']['trigger_phrase'])
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

# constants
VAD_SAMPLERATE = 16000
VAD_FRAME_MS = 30
VAD_PERIOD = (VAD_SAMPLERATE / 1000) * VAD_FRAME_MS
VAD_SILENCE_TIMEOUT = 1000
VAD_THROWAWAY_FRAMES = 10
MAX_RECORDING_LENGTH = 8
MAX_VOLUME = 100
MIN_VOLUME = 30



def internet_on():
	print("Checking Internet Connection...")
	try:
		r = requests.get('https://api.amazon.com/auth/o2/token')
		print("Connection {}OK{}".format(bcolors.OKGREEN, bcolors.ENDC))
		return True
	except:
		print("Connection {}Failed{}".format(bcolors.WARNING, bcolors.ENDC))
		return False

def gettoken():
	token = mc.get("access_token")
	refresh = config['alexa']['refresh_token']

	if token:
		return token

	elif refresh:
		payload = {"client_id" : config['alexa']['Client_ID'], "client_secret" : config['alexa']['Client_Secret'], "refresh_token" : refresh, "grant_type" : "refresh_token", }
		url = "https://api.amazon.com/auth/o2/token"
		r = requests.post(url, data = payload)
		resp = json.loads(r.text)
		mc.set("access_token", resp['access_token'], 3570)
		return resp['access_token']

	else:
		return False


def alexa_speech_recognizer():
	# https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/speechrecognizer-requests
	if debug: print("{}Sending Speech Request...{}".format(bcolors.OKBLUE, bcolors.ENDC))
	# GPIO.output(config['raspberrypi']['plb_light'], GPIO.HIGH)
	url = 'https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize'
	headers = {'Authorization' : 'Bearer %s' % gettoken()}
	d = {
		"messageHeader": {
			"deviceContext": [
				{
					"name": "playbackState",
					"namespace": "AudioPlayer",
					"payload": {
					"streamId": "",
						"offsetInMilliseconds": "0",
						"playerActivity": "IDLE"
					}
				}
			]
		},
		"messageBody": {
			"profile": "alexa-close-talk",
			"locale": "en-us",
			"format": "audio/L16; rate=16000; channels=1"
		}
	}
	with open(tmp_path + 'recording.wav') as inf:
		files = [
				('file', ('request', json.dumps(d), 'application/json; charset=UTF-8')),
				('file', ('audio', inf, 'audio/L16; rate=16000; channels=1'))
				]
		r = requests.post(url, headers=headers, files=files)
	process_response(r)
	

def alexa_getnextitem(nav_token):
	# https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/audioplayer-getnextitem-request
	time.sleep(0.5)
        if not player.is_avr_playing():
		if debug: print("{}Sending GetNextItem Request...{}".format(bcolors.OKBLUE, bcolors.ENDC))
		# GPIO.output(config['raspberrypi']['plb_light'], GPIO.HIGH)
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
	if debug: print("{}Sending Playback Progress Report Request...{}".format(bcolors.OKBLUE, bcolors.ENDC))
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
		print("{}(alexa_playback_progress_report_request Response){} {}".format(bcolors.WARNING, bcolors.ENDC, r))
	else:
		if debug: print("{}Playback Progress Report was {}Successful!{}".format(bcolors.OKBLUE, bcolors.OKGREEN, bcolors.ENDC))

def process_response(r):
	if debug: print("{}Processing Request Response...{}".format(bcolors.OKBLUE, bcolors.ENDC))
	pstate.nav_token = ""
	pstate.streamurl = ""
	pstate.streamid = ""
	if r.status_code == 200:
		data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
		msg = email.message_from_string(data)
		for payload in msg.get_payload():
			if payload.get_content_type() == "application/json":
				j =  json.loads(payload.get_payload())
				if debug: print("{}JSON String Returned:{} {}".format(bcolors.OKBLUE, bcolors.ENDC, json.dumps(j)))
			elif payload.get_content_type() == "audio/mpeg":
				filename = tmp_path + payload.get('Content-ID').strip("<>")+".mp3"
				with open(filename, 'wb') as f:
					f.write(payload.get_payload())
			else:
				if debug: print("{}NEW CONTENT TYPE RETURNED: {} {}".format(bcolors.WARNING, bcolors.ENDC, payload.get_content_type()))
		# Now process the response
		if 'directives' in j['messageBody']:
			if len(j['messageBody']['directives']) == 0:
				if debug: print("0 Directives received")
				GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)
				GPIO.output(config['raspberrypi']['plb_light'], GPIO.LOW)
			for directive in j['messageBody']['directives']:
				if directive['namespace'] == 'SpeechSynthesizer':
					if directive['name'] == 'speak':
						GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)
						player.play_avr("file://" + tmp_path + directive['payload']['audioContent'].lstrip("cid:")+".mp3")
					for directive in j['messageBody']['directives']: # if Alexa expects a response
						if directive['namespace'] == 'SpeechRecognizer': # this is included in the same string as above if a response was expected
							if directive['name'] == 'listen':
								if debug: print("{}Further Input Expected, timeout in: {} {}ms".format(bcolors.OKBLUE, bcolors.ENDC, directive['payload']['timeoutIntervalInMillis']))
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
								content = "file://" + tmp_path + stream['streamUrl'].lstrip("cid:")+".mp3"
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
						if debug: print("new volume = {}".format(pstate.currVolume))
						
		elif 'audioItem' in j['messageBody']: 			#Additional Audio Iten
			pstate.nav_token = j['messageBody']['navigationToken']
			for stream in j['messageBody']['audioItem']['streams']:
				if stream['progressReportRequired']:
					pstate.streamid = stream['streamId']
				if stream['streamUrl'].startswith("cid:"):
					content = "file://" + tmp_path + stream['streamUrl'].lstrip("cid:")+".mp3"
				else:
					content = stream['streamUrl']
				pThread = threading.Thread(target=player.play_media, args=(content, stream['offsetInMilliseconds']))
				pThread.start()

		return
	elif r.status_code == 204:
		GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)
		for x in range(0, 3):
			time.sleep(.2)
			GPIO.output(config['raspberrypi']['plb_light'], GPIO.HIGH)
			time.sleep(.2)
			GPIO.output(config['raspberrypi']['plb_light'], GPIO.LOW)
		player.resume_media_player()
		if debug: print("{}Request Response is null {}(This is OKAY!){}".format(bcolors.OKBLUE, bcolors.OKGREEN, bcolors.ENDC))
	else:
		print("{}(process_response Error){} Status Code: {}".format(bcolors.WARNING, bcolors.ENDC, r.status_code))
		r.connection.close()
		GPIO.output(config['raspberrypi']['lights'], GPIO.LOW)
		for x in range(0, 3):
			time.sleep(.2)
			GPIO.output(config['raspberrypi']['rec_light'], GPIO.HIGH)
			time.sleep(.2)
			GPIO.output(config['raspberrypi']['lights'], GPIO.LOW)

		
def tuneinplaylist(url):
	global tunein_parser
	if (debug): print("TUNE IN URL = {}".format(url))
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
        if debug: print("{}Button Pressed! Recording...{}".format(bcolors.OKBLUE, bcolors.ENDC))
        time.sleep(.5) # time for the button input to settle down
        while (GPIO.input(config['raspberrypi']['button'])==0):
                button_pressed = True
                time.sleep(.1)
                if time.time() - buttonPress > 10: # pressing button for 10 seconds triggers a system halt
                	player.play_avr(resources_path+'alexahalt.mp3')
                	if debug: print("{} -- 10 second putton press.  Shutting down. -- {}".format(bcolors.WARNING, bcolors.ENDC))
                	os.system("halt")
        if debug: print("{}Recording Finished.{}".format(bcolors.OKBLUE, bcolors.ENDC))
        button_pressed = False
        time.sleep(.5) # more time for the button to settle down

def silence_listener(throwaway_frames):
		global button_pressed
		# Reenable reading microphone raw data
		inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, config['sound']['device'])
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
			GPIO.output(config['raspberrypi']['rec_light'], GPIO.HIGH)

		if debug: print ("Debug: End recording")

		# if debug: player.play_avr(resources_path+'beep.wav', 0, 100)

		GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)
		rf = open(tmp_path + 'recording.wav', 'w')
		rf.write(audio)
		rf.close()
		inp.close()


def start():
	global vad, button_pressed
	GPIO.add_event_detect(config['raspberrypi']['button'], GPIO.FALLING, callback=detect_button, bouncetime=100) # threaded detection of button press
	while True:
		record_audio = False

		# Enable reading microphone raw data
		inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, config['sound']['device'])
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
		if debug: print ("detected the edge, setting up audio")

		# To avoid overflows close the microphone connection
		inp.close()

		# clean up the temp directory
		if debug == False:
			for file in os.listdir(tmp_path):
				file_path = os.path.join(tmp_path, file)
				try:
					if os.path.isfile(file_path):
						os.remove(file_path)
				except Exception as e:
					print(e)

		if debug: print "Starting to listen..."
		silence_listener(VAD_THROWAWAY_FRAMES)

		if debug: print "Debug: Sending audio to be processed"
		alexa_speech_recognizer()

		# Now that request is handled restart audio decoding
		decoder.end_utt()


def cleanup(signal, frame):
	shutil.rmtree(tmp_path)
	sys.exit(0)


def setup():
	for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
		signal.signal(sig, cleanup)

	GPIO.setwarnings(False)
	GPIO.cleanup()
	GPIO.setmode(GPIO.BCM)

	player.setup(alexa_playback_progress_report_request, alexa_getnextitem, tuneinplaylist)

	GPIO.setup(config['raspberrypi']['button'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(config['raspberrypi']['lights'], GPIO.OUT)
	GPIO.output(config['raspberrypi']['lights'], GPIO.LOW)
	while internet_on() == False:
		print(".")
	token = gettoken()
	if token == False:
		while True:
			for x in range(0, 5):
				time.sleep(.1)
				GPIO.output(config['raspberrypi']['rec_light'], GPIO.HIGH)
				time.sleep(.1)
				GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)
	for x in range(0, 5):
		time.sleep(.1)
		GPIO.output(config['raspberrypi']['plb_light'], GPIO.HIGH)
		time.sleep(.1)
		GPIO.output(config['raspberrypi']['plb_light'], GPIO.LOW)
	if (silent == False): player.play_avr(resources_path+"hello.mp3")


if __name__ == "__main__":
	a = session.http2_connection(config)
	#print a.get_auth_token()

	#setup()
	#start()
