#alexapi/player/player.py

import vlc
import time
import threading
from collections import deque

from alexapi.shared import *

player = None
alexa_playback_progress_report_request = None
alexa_getnextitem = None
tuneinplaylist = None

avr_playing = False
media_playing = False
media_paused = False

class PlayerState:
	class MediaInfo:
		content = None
		token = None
		play_behavior = None
		url = None
		nav_token = None
		streamFormat = None
		offset = None

	__mediaInfo = {}
	nav_token = "" #TODO: remove "" checks in callback
	streamurl = ""
	streamid = ""
	audioplaying = False
	currVolume = 100
	queue_position = 0
	queueplaying = False
	currentItem = False
	overRideVolume = 0
	queue_almost_empty = False

	def clr_mediaInfo(self):
		self.__mediaInfo.clear()

	def get_mediaInfoItem(self, key, item):
		value = getattr(self.__mediaInfo[key], item, False)
		if not value:
			raise NotImplementedError('%s - does not exist!', item)
		return value

	def get_mediaInfo(self, key):
		return self.__mediaInfo[key]

	def add_mediaInfo(self, **kwargs):
		mi = self.MediaInfo()
		for k,v in kwargs.iteritems():
			setattr(mi, k, v)

		print '\nKey: %s' % mi.nav_token
		for k,v in kwargs.iteritems():
			print 'Setting: %s = %s' % (k, v)
		print

		return self.__mediaInfo.update({mi.nav_token:mi})

	def del_mediaInfo(self, key):
		r = dict(self.__mediaInfo)
		del r[key]
		return r

class AlexaVoiceResponsePlayer(object):
	instance = None
	player = None


	def __init__(self):
		self.instance = vlc.Instance('--aout=alsa') # , '--alsa-audio-device=mono', '--file-logging', '--logfile=vlc-log.txt')


	def play(self, file, callback=False, overRideVolume=0):
		global avr_playing
		if debug: print("\n{}Alexa Voice Response_Player Request for:{} {}".format(bcolors.OKBLUE, bcolors.ENDC, file))
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
			#if debug: print("{}Get from queue:{} {} | Count: {}".format(bcolors.OKBLUE, bcolors.ENDC, self.currentItem, sum(1 for i in self.q)))
			return self.currentItem
		else:
			return None

	def getItemCount(self):
		return sum(1 for i in self.q)


	def queue_and_play(self, nav_token, callback=False):
		global media_playing, media_paused
		#TODO: add volumue override

		if file:
			#self.addItem(file)
			self.addItem(nav_token)

		while True:
			if media_playing is False and media_paused is False:
				pstate.currentItem = nav_token
				media_paused = False
				media_playing = True

				if self.getItemCount() == 1: # 1 queue item left
					pstate.queue_almost_empty = True

				elif self.getItemCount() > 1: # 1 queue item left
					pstate.queue_almost_empty = False

				self.player = self.instance.media_player_new()
				media = self.instance.media_new(pstate.get_mediaInfoItem(self.getNextItem(), 'content'))
				self.player.set_media(media)
				events = media.event_manager()
				events.event_attach(vlc.EventType.MediaStateChanged, self.media_player_callback, self.player, callback)

				if (pstate.overRideVolume == 0):
					self.player.audio_set_volume(pstate.currVolume)
				else:
					self.player.audio_set_volume(pstate.overRideVolume)

				if debug: print "\n{}{}Play media:{} {} | Count: {}".format(bcolors.BOLD, bcolors.OKBLUE, bcolors.ENDC, self.getCurrentItem(), self.getItemCount())
				self.player.play()
				time.sleep(.1) # Allow time for state_callback to run


				while media_playing: #Wait until current media clip is done playing
					time.sleep(.5) #Prevent 100% CPU untilzation
					continue

				if self.getItemCount() == 0: # No more items in queue. Quit loop
					pstate.clr_mediaInfo()
					pstate.currentItem = False
					break

	def clear_queue(self, clear_type):
		self.q.clear()
		if clear_type == 'CLEAR_ALL':
			if self.player:
				self.player.stop()

	def stop(self):
		if self.player:
			self.player.stop()

	def resume(self):
		queue_and_play(self)

	def is_playing(self):
		global media_playing
		return media_playing


	def media_player_callback(self, event, player, callback=False):
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

		elif state == 7:	#Error
			media_playing = False


		if callback:
			callback(state)

		if state == 3 and not self.getItemCount() == 0 and pstate.queue_almost_empty:
			callback(8) #Send playback almost empty



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
#def play_media(file, offset=0, overRideVolume=0, callback=False):
def play_media(nav_token, callback=False):
	media_player.queue_and_play(nav_token, callback)

def resume_media_player():
	media_player.resume()

def pause_media_player():
	media_player.pause()

def clear_queue_media_player(clear_type):
	media_player.clear_queue(clear_type)

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



pstate = PlayerState()
