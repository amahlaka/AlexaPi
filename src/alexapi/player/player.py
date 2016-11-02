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

media_playing = False
media_paused = False

class PlayerState:
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

	class MediaInfo:
		content = None
		token = None
		play_behavior = None
		url = None
		nav_token = None
		streamFormat = None
		offset = None



	def clr(self):
		self.__mediaInfo.clear()

	def get(self, key, item):
		value = getattr(self.__mediaInfo[key], item, False)
		if not value:
			raise NotImplementedError('%s - does not exist!', item)
		return value

	def get_all(self, key):
		return self.__mediaInfo[key]

	def add(self, **kwargs):
		mi = self.MediaInfo()
		for k,v in kwargs.iteritems():
			setattr(mi, k, v)

		print '\nKey: %s' % mi.nav_token
		for k,v in kwargs.iteritems():
			print 'Setting: %s = %s' % (k, v)
		print

		return self.__mediaInfo.update({mi.nav_token:mi})

	def rm(self, key):
		r = dict(self.__mediaInfo)
		del r[key]
		return r

state = PlayerState()


class MediaPlayer():
	__vlc_instance = None
	__player = None
	__queue = None

	class __Queue():
		q = None

		def __init__(self):
			q = deque() #A Thread safe queue used to play audio files play sequencially (FIFO)

		def addItem(self, item):
			global tuneinplaylist

			if (item.find('radiotime.com') != -1):
				item = tuneinplaylist(item)

			self.q.appendleft(item)
			if debug: print("{}Add to queue:{} {} | Count: {}".format(bcolors.OKBLUE, bcolors.ENDC, item, sum(1 for i in self.q)))



		def getNextItem(self):
			if self.q:
				self.currentItem = self.q.pop()
				#if debug: print("{}Get from queue:{} {} | Count: {}".format(bcolors.OKBLUE, bcolors.ENDC, self.currentItem, sum(1 for i in self.q)))
				return self.currentItem
			else:
				return None

		def getItemCount(self):
			return sum(1 for i in self.q)

	def __init__(self, avr=False):
		self.__vlc_instance = vlc.Instance('--aout=alsa') # , '--alsa-audio-device=mono', '--file-logging', '--logfile=vlc-log.txt')
		if not avr:
			self.__queue = self.__Queue()
		else:
			self.__queue = False

	def __callback(self, event, player, callback=False):
		global media_playing, alexa_playback_progress_report_request, alexa_getnextitem

		vlc_state = player.get_state()

		if debug: print("{}Media Player State:{} {}".format(bcolors.OKGREEN, bcolors.ENDC, state))

		if vlc_state == 3:		#Playing
			media_playing = True
			media_paused = False

		elif vlc_state == 4:	#Paused
			media_playing = False
			media_paused = True

		elif vlc_state == 5:	#Stopped
			media_playing = False

		elif vlc_state == 6:	#Ended
			media_playing = False

		elif vlc_state == 7:	#Error
			media_playing = False


		if callback:
			callback(vlc_state)

		if vlc_state == 3 and not self.__queue.getItemCount() == 0 and vlc_state.queue_almost_empty:
			callback(8) #Send playback almost empty

	def queue_and_play(self, token, callback=False):
		global media_playing, media_paused
		#TODO: add volumue override

		if token:
			#self.addItem(file)
			self.__queue.addItem(token)

		while True:
			if media_playing is False and media_paused is False:
				state.currentItem = token
				media_paused = False
				media_playing = True

				if self.getItemCount() == 1: # 1 queue item left
					state.queue_almost_empty = True

				elif self.getItemCount() > 1: # 1 queue item left
					state.queue_almost_empty = False

				self.player = self.vlc_instance.media_player_new()
				media = self.vlc_instance.media_new(state.get(self.__queue.getNextItem(), 'content'))
				self.player.set_media(media)
				events = media.event_manager()
				events.event_attach(vlc.EventType.MediaStateChanged, self.__callback, self.player, callback)

				if (state.overRideVolume == 0):
					self.player.audio_set_volume(state.currVolume)
				else:
					self.player.audio_set_volume(state.overRideVolume)

				if debug: print "\n{}{}Play media:{} {} | Count: {}".format(bcolors.BOLD, bcolors.OKBLUE, bcolors.ENDC, state.currentItem, self.__queue.getItemCount())
				self.player.play()
				time.sleep(.1) # Allow time for state_callback to run


				while media_playing: #Wait until current media clip is done playing
					time.sleep(.5) #Prevent 100% CPU untilzation
					continue

				if self.getItemCount() == 0: # No more items in queue. Quit loop
					state.clr()
					state.currentItem = False
					break

	def clear_queue(self, clear_type):
		self.__queue.clear()
		if clear_type == 'CLEAR_ALL':
			if self.player:
				self.player.stop()

	def stop(self):
		if self.player:
			self.player.stop()

	def resume(self): #TODO: Probably broken
		queue_and_play(self)

	def is_playing(self):
		global media_playing
		return media_playing

	def getCurrentItem(self):
		return state.currentItem

# Initialize players
media = MediaPlayer()
avr = MediaPlayer(True)

"""
Setup
"""
def setup(playback_progress_report_request, getnextitem, tplaylist):	#TODO:I'm sure there is a better way
	global alexa_playback_progress_report_request, alexa_getnextitem, tuneinplaylist

	tuneinplaylist = tplaylist
	alexa_playback_progress_report_request=playback_progress_report_request
	alexa_getnextitem = getnextitem
