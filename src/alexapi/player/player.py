#alexapi/player/player.py

import vlc
import time
import threading
from collections import deque

from alexapi.shared import *
import alexapi.player.player_state as pstate

player = None
alexa_playback_progress_report_request = None
alexa_getnextitem = None
tuneinplaylist = None

avr_playing = False
media_playing = False
media_paused = False

class AlexaVoiceResponsePlayer(object):
	instance = None
	player = None


	def __init__(self):
		self.instance = vlc.Instance('--aout=alsa') # , '--alsa-audio-device=mono', '--file-logging', '--logfile=vlc-log.txt')


	def play(self, file, callback=False, overRideVolume=0):
		global avr_playing
		if debug: print("{}Alexa Voice Response_Player Request for:{} {}".format(bcolors.OKBLUE, bcolors.ENDC, file))
		led.status_on()

		self.player = self.instance.media_player_new()
		media = self.instance.media_new(file)
		self.player.set_media(media)

		events = media.event_manager()
		events.event_attach(vlc.EventType.MediaStateChanged, self.avrp_callback, self.player, callback)

		if (overRideVolume == 0):
			self.player.audio_set_volume(pstate.currVolume)
		else:
			self.player.audio_set_volume(overRideVolume)

		self.player.play()
		time.sleep(.1) # Allow time for state_callback to run

		while avr_playing:
			time.sleep(.1) # Prevent 100% CPU untilzation
			continue

		led.status_off()


	def stop(self):
		self.player.stop()


	def is_playing(self):
		global avr_playing
		return avr_playing


	def avrp_callback(self, event, player, callback=False):
		global avr_playing, alexa_playback_progress_report_request, alexa_getnextitem

		state = player.get_state()

		#0: 'NothingSpecial'
		#1: 'Opening'
		#2: 'Buffering'
		#3: 'Playing'
		#4: 'Paused'
		#5: 'Stopped'
		#6: 'Ended'
		#7: 'Error'

		if debug: print("{}Alexa Repsonse Player State:{} {}".format(bcolors.OKGREEN, bcolors.ENDC, state))
		if state == 3:		#Playing
			avr_playing = True
			if pstate.streamid != "":
				rThread = threading.Thread(target=alexa_playback_progress_report_request, args=("STARTED", "PLAYING", pstate.streamid))
				rThread.start()

		elif state == 5:	#Stopped
			avr_playing = False
			if pstate.streamid != "":
				rThread = threading.Thread(target=alexa_playback_progress_report_request, args=("INTERRUPTED", "IDLE", pstate.streamid))
				rThread.start()
			pstate.streamurl = ""
			pstate.streamid = ""
			pstate.nav_token = ""

		elif state == 6:	#Ended
			avr_playing = False
			if pstate.streamid != "":
				rThread = threading.Thread(target=alexa_playback_progress_report_request, args=("FINISHED", "IDLE", pstate.streamid))
				rThread.start()
				pstate.streamid = ""

			if pstate.streamurl != "":
				pThread = threading.Thread(target=play, args=(pstate.streamurl,))
				pThread.start()
				pstate.streamurl = ""

			#elif pstate.nav_token != "":
			#	gThread = threading.Thread(target=alexa_getnextitem, args=(pstate.nav_token,))
			#	gThread.start()

		elif state == 7:
			avr_playing = False
			if pstate.streamid != "":
				rThread = threading.Thread(target=alexa_playback_progress_report_request, args=("ERROR", "IDLE", pstate.streamid))
				rThread.start()

			pstate.streamurl = ""
			pstate.streamid = ""
			pstate.nav_token = ""

		if callback:
			callback(state)


class MediaPlayer(object):
	q = deque() #A Thread safe queue used to play audio files play sequencially (FIFO)

	instance = None
	player = None


	def __init__(self):
		self.instance = vlc.Instance('--aout=alsa') # , '--alsa-audio-device=mono', '--file-logging', '--logfile=vlc-log.txt')


	def addItem(self, item):
		global tuneinplaylist

		if (item.find('radiotime.com') != -1):
			item = tuneinplaylist(item)

		self.q.appendleft(item)
		if debug: print("{}Add to queue:{} {} | Count: {}".format(bcolors.OKBLUE, bcolors.ENDC, item, sum(1 for i in self.q)))


	def getCurrentItem(self):
		return self.currentItem


	def getNextItem(self):
		if self.q:
			self.currentItem = self.q.pop()
			if debug: print("{}Get from queue:{} {} | Count: {}".format(bcolors.OKBLUE, bcolors.ENDC, self.currentItem, sum(1 for i in self.q)))
			return self.currentItem
		else:
			return None


	def getItemCount(self):
		return sum(1 for i in self.q)


	def queue_and_play(self, file, offset=0, overRideVolume=0):
		global media_playing, media_paused
		#TODO: add volumue override

		if file:
			self.addItem(file)

		while True:
			if media_playing is False and media_paused is False:
				media_paused = False

				if self.getItemCount() == 0: # No more items in queue. Quit loop
					#TODO: Do stuff
					break

				media_playing = True

				self.player = self.instance.media_player_new()
				media = self.instance.media_new(self.getNextItem())
				self.player.set_media(media)
				events = media.event_manager()
				events.event_attach(vlc.EventType.MediaStateChanged, self.media_player_callback, self.player)

				if (overRideVolume == 0):
					self.player.audio_set_volume(pstate.currVolume)
				else:
					self.player.audio_set_volume(overRideVolume)

				if debug: print "{}Queue playing:{} {}".format(bcolors.OKBLUE, bcolors.ENDC, self.getCurrentItem())
				self.player.play()
				time.sleep(.1) # Allow time for state_callback to run


				while media_playing:
					time.sleep(.5) # Prevent 100% CPU untilzation
					continue

				#TODO: Do I still need this? 
				#media_playing = False

			time.sleep(1) # Prevent 100% CPU untilzation


	def stop(self):
		self.q.clear()
		self.player.stop()

	def resume(self):
		queue_and_play(self)

	def is_playing(self):
		global media_playing
		return media_playing


	def media_player_callback(self, event, player):
		global media_playing, alexa_playback_progress_report_request, alexa_getnextitem

		state = player.get_state()

		if debug: print("{}Media Player State:{} {}".format(bcolors.OKGREEN, bcolors.ENDC, state))
		if state == 3:		#Playing
			media_playing = True
			media_paused = False

		elif state == 4:	#Paused
			media_playing = False
			media_paused = True

		elif state == 5:	#Stopped
			media_playing = False

		elif state == 6:	#Ended
			media_playing = False
			if pstate.streamid != "":
				rThread = threading.Thread(target=alexa_playback_progress_report_request, args=("FINISHED", "IDLE", pstate.streamid))
				rThread.start()
				pstate.streamid = ""

			if pstate.streamurl != "":
				pThread = threading.Thread(target=play, args=(pstate.streamurl,))
				pThread.start()
				pstate.streamurl = ""

			elif pstate.nav_token != "":
				gThread = threading.Thread(target=alexa_getnextitem, args=(pstate.nav_token,))
				gThread.start()

		elif state == 7:	#Error
			media_playing = False


# Initialize players
alexa_voice_response_player = AlexaVoiceResponsePlayer()
media_player = MediaPlayer()


"""
Setup
"""
def setup(playback_progress_report_request, getnextitem, tplaylist):	#TODO:I'm sure there is a better way
	global alexa_playback_progress_report_request, alexa_getnextitem, tuneinplaylist

	tuneinplaylist = tplaylist
	alexa_playback_progress_report_request=playback_progress_report_request
	alexa_getnextitem = getnextitem

"""
Audio Player Methods
"""
def play_media(file, offset=0, overRideVolume=0):
	media_player.queue_and_play(file, offset, overRideVolume)

def resume_media_player():
	media_player.resume()

def pause_media_player():
	media_player.pause()


def stop_media_player():
	media_player.stop()


def is_media_playing():
	return media_player.is_playing()


def is_media_paused():
	return media_player.is_paused()


"""
Alexa Voice Response Player Methods
"""
def play_avr(file, callback=False, overRideVolume=0):
	alexa_voice_response_player.play(file, callback, overRideVolume)


def stop_avr():
	alexa_voice_response_player.stop()


def is_avr_playing():
	return alexa_voice_response_player.is_playing()
