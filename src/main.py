#! /usr/bin/env python

import os
import sys
import time
import alsaaudio
import webrtcvad
import traceback

from pocketsphinx import get_model_path
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *

from alexa import alexa
from alexa.avs.interface_manager import InterfaceManager
import alexa.exit_handler as exit_handler

#Get logging
log = alexa.logger('Alexa.main')

#Setup
recorded = False

# PocketSphinx configuration
ps_config = Decoder.default_config()

# Set recognition model to US
ps_config.set_string('-hmm', os.path.join(get_model_path(), 'en-us'))
ps_config.set_string('-dict', os.path.join(get_model_path(), 'cmudict-en-us.dict'))

#Specify recognition key phrase
ps_config.set_string('-keyphrase', alexa.config['sphinx']['trigger_phrase'])
ps_config.set_float('-kws_threshold',1e-5)

# Hide the VERY verbose logging information
ps_config.set_string('-logfn', '/dev/null')

# Process audio chunk by chunk. On keyword detected perform action and restart search
decoder = Decoder(ps_config)

#Variables
button_pressed = False
start = time.time()
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


def detect_button(channel):
        global button_pressed
        buttonPress = time.time()
        button_pressed = True
        log.info("{}Button Pressed! Recording...{}".format(alexa.bcolors.OKBLUE, alexa.bcolors.ENDC))
        time.sleep(.5) # time for the button input to settle down
        while (alexa.get_button_status() == 0):
                button_pressed = True
                time.sleep(.1)
                if time.time() - buttonPress > 10: # pressing button for 10 seconds triggers a system halt
			alexa.playback.halt()
			log.info("{} -- 10 second putton press.  Shutting down. -- {}".format(alexa.bcolors.WARNING, alexa.bcolors.ENDC))
			os.system("halt")

        log.debug("{}Recording Finished.{}".format(alexa.bcolors.OKBLUE, alexa.bcolors.ENDC))
        button_pressed = False
        time.sleep(.5) # more time for the button to settle down

def silence_listener(throwaway_frames):
		global button_pressed
		# Reenable reading microphone raw data
		inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, alexa.config['sound']['device'])
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

		# now do VAD
		while button_pressed == True or ((thresholdSilenceMet == False) and ((time.time() - start) < MAX_RECORDING_LENGTH)):
			l, data = inp.read()
			if l:
				audio += data

				if (l == VAD_PERIOD):
					isSpeech = vad.is_speech(data, VAD_SAMPLERATE)

					if (isSpeech == False):
						silenceRun = silenceRun + 1
					else:
						silenceRun = 0
						numSilenceRuns = numSilenceRuns + 1

			# only count silence runs after the first one
			# (allow user to speak for total of max recording length if they haven't said anything yet)
			if (numSilenceRuns != 0) and ((silenceRun * VAD_FRAME_MS) > VAD_SILENCE_TIMEOUT):
				thresholdSilenceMet = True
			alexa.led.rec_on()

		log.debug("Debug: End recording")
		if alexa.debug: alexa.playback.beep()

		alexa.led.rec_off()
		rf = open(alexa.tmp_path + 'recording.wav', 'w')
		rf.write(audio)
		rf.close()
		inp.close()

def start():
	global vad, button_pressed, avs_interface
	alexa.Button(detect_button)

	while True:
		record_audio = False

		# Enable reading microphone raw data
		inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, alexa.config['sound']['device'])
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
				if alexa.player.is_playing():
					alexa.player.stop()
					time.sleep(.5) #add delay before audio prompt

				start = time.time()
				record_audio = True
				alexa.playback.yes()

			elif button_pressed:
				if alexa.player.is_playing: player.stop()
				record_audio = True

		# do the following things if either the button has been pressed or the trigger word has been said
		log.debug("detected the edge, setting up audio")

		# To avoid overflows close the microphone connection
		inp.close()

		# clean up the temp directory
		if alexa.debug == False:
			for file in os.listdir(alexa.tmp_path):
				file_path = os.path.join(alexa.tmp_path, file)
				try:
					if os.path.isfile(file_path):
						os.remove(file_path)
				except Exception as e:
					log.execption(e)

		log.info("Starting to listen...")
		silence_listener(VAD_THROWAWAY_FRAMES)

		log.debug("Debug: Sending audio to be processed")
		avs_interface.trigger_event('SpeechRecognizer', 'Recognize') # https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/rest/speechrecognizer-requests

		# Now that request is handled restart audio decoding
		decoder.end_utt()

def setup():
	global avs_interface, exit
	exit = exit_handler.CleanUp(alexa.tmp_path)
	avs_interface = InterfaceManager()
	if (alexa.silent == False): alexa.playback.hello()

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
