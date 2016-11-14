#alexa/player/player.py

import vlc
import time
from collections import deque

import alexa
from alexa.player import tunein
from alexa.thread import thread_manager
from alexa.avs.interface_state_manager import StateManager

log = alexa.logger.getLogger(__name__)
tunein_parser = tunein.TuneIn(5000)

media_playing = False
media_paused = False


class StateDiagram:
	IDLE		= 0
	PLAYING		= 1
	STOPPED		= 2
	PAUSED		= 3
	BUFFER_UNDERRUN	= 4
	FINISHED	= 5

class GlobalMediaState:
	def __init__(self):
		self.current_item = None
		self.current_token = None
		self.current_state = StateDiagram.IDLE

gstate = GlobalMediaState()

class PlaybackDataContainer(object):
	class _Container(dict):
		def __setitem__(self, key, value):
			dict.__setitem__(self, key, value)

		def __getitem__(self, key):
			value = dict.__getitem__(self, key)
			return value

	def __init__(self, **kwargs):
		self._data = self._Container(kwargs)
		for k,v in kwargs.iteritems():
			setattr(self._data, k, v)

	@property
	def data(self):
		return self._data

class MediaPlayer():

	class _Settings:
		currVolume = 100
		overRideVolume = 0

	class _MediaPackage:

		class MediaInfo:
			content = None
			token = None
			play_behavior = None
			url = None
			nav_token = None
			streamFormat = None
			offset = None

		def __init__(self):
			self._mediaInfo = {}

		def clr(self):
			self._mediaInfo.clear()

		def get(self, key, item):
			value = getattr(self._mediaInfo[key], item, False)
			if not value:
				raise NotImplementedError('%s - does not exist!', item)
			return value

		def get_all(self, key):
			return self._mediaInfo[key]

		def add(self, **kwargs):
			mi = self.MediaInfo()
			for k,v in kwargs.iteritems():
				setattr(mi, k, v)

			if not mi.token:
				raise NotImplementedError('A unique key called "token" is required!')

			return self._mediaInfo.update({mi.token:mi})

		def rm(self, key):
			r = dict(self._mediaInfo)
			del r[key]
			return r

	class _Queue():

		def __init__(self):
			self._q = deque() #A Thread safe queue used to play audio files play sequencially (FIFO)
			self._item_count = 0

		def addItem(self, item):
			self._q.appendleft(item)
			self._item_count =  sum(1 for i in self._q)
			log.info("{}Add to queue:{} {} | Items remaining in queue: {}".format(log.color.OKBLUE, log.color.ENDC, item, self._item_count))

		def getNextItem(self):
			if self._q:
				current_item = self._q.pop()
				self._item_count -= 1
				return current_item
			else:
				return None

		def getItemCount(self):
			return self._item_count

	def __init__(self):
		self.avs_playback = PlaybackDataContainer(token=None, is_playing=False, is_paused=False, vlc_player=None, interface_callback=True, queue_almost_empty=False)
		self._state_manager = StateManager()
		self.audio_player_interface = False
		self.package = self._MediaPackage()
		self._settings = self._Settings()
		self._vlc_instance = vlc.Instance('--aout=alsa') # , '--alsa-audio-device=mono', '--file-logging', '--logfile=vlc-log.txt')
		self._queue = self._Queue()


	def _tuneinplaylist(self, url):
		global tunein_parser
		log.debug("TUNE IN URL = {}".format(url))
		req = requests.get(url)
		lines = req.content.split('\n')

		nurl = tunein_parser.parse_stream_url(lines[0])
		if (len(nurl) != 0):
			return nurl[0]

		return ""

	def bind(self, audio_player_interface):
		if audio_player_interface:
			self.audio_player_interface = audio_player_interface

	def play_local(self, file, overRideVolume=0):
		playback = PlaybackDataContainer(is_playing=False, vlc_player=None, interface_callback=False)
		playback.data['caller_name'] = 'play_local'

		if playback.data['is_playing'] is False:
			playback.is_playing = True

			playback.data['vlc_player'] = self._vlc_instance.media_player_new()
			media = self._vlc_instance.media_new(file)
			playback.data['vlc_player'].set_media(media)
			events = media.event_manager()
			events.event_attach(vlc.EventType.MediaStateChanged, self._state_manager.callback, playback)

			if (overRideVolume == 0):
				playback.data['vlc_player'].audio_set_volume(self._settings.currVolume)
			else:
				playback.data['vlc_player'].audio_set_volume(overRideVolume)

			log.info('Play local media: %s', (file,))
			playback.data['vlc_player'].play()
			time.sleep(.1) # Allow time for state_callback to run

			while playback.data['is_playing']: #Wait until current media clip is done playing
				time.sleep(.1) #Prevent 100% CPU untilzation and adds a slight pause between alexa responses
				continue

	def play_avs_response(self, token, override_volume=0):
		def play(token, override_volume):
			self.avs_playback.data['caller_name'] = 'play_avs_response'

			if token:
				self.avs_playback.data['token'] = token
				self._queue.addItem(token)

			while self._queue.getItemCount() > 0:
				self.avs_playback.data['type'] = 'remote'

				if self.avs_playback.data['is_playing'] is False and self.avs_playback.data['is_paused'] is False:
					self.avs_playback.data['is_playing'] = True
					self.avs_playback.data['is_paused'] = False
					self.avs_playback.data['token'] = token

					gstate.current_token = token

					content = self.package.get(self._queue.getNextItem(), 'content')
					gstate.current_item = content
					self.avs_playback.data['current_item'] = content

					if self._queue.getItemCount() > 1: # 1 queue item left
						self.avs_playback.data['queue_almost_empty'] = False

					elif self._queue.getItemCount() == 1: # 1 queue item left
						self.avs_playback.data['queue_almost_empty'] = True

					self.avs_playback.data['vlc_player'] = self._vlc_instance.media_player_new()
					if (content.find('radiotime.com') != -1):
						content = self._tuneinplaylist(content)

					media = self._vlc_instance.media_new(content)
					self.avs_playback.data['vlc_player'].set_media(media)
					events = media.event_manager()
					events.event_attach(vlc.EventType.MediaStateChanged, self._state_manager.callback, self.avs_playback)

					print '******' + str(override_volume)
					if (override_volume == 0):
						self.avs_playback.data['vlc_player'].audio_set_volume(self._settings.currVolume)
					else:
						self.avs_playback.data['vlc_player'].audio_set_volume(override_volume)

					log.info("{}{}Play retrieved media:{} {} | Items remaining in queue: {}".format(log.color.BOLD, log.color.OKBLUE, log.color.ENDC, gstate.current_item, self._queue.getItemCount()))
					self.avs_playback.data['vlc_player'].play()
					time.sleep(.1) # Allow time for state_callback to run

					while self.avs_playback.data['is_playing']: #Wait until current media clip is done playing
						time.sleep(.5) #Prevent 100% CPU untilzation
						continue

		thread_manager.start(play, self.stop, token, override_volume)

	def clear_queue(self, clear_type, callback):
		self._queue.clear()
		if clear_type == 'CLEAR_ALL':
			if self.avs_playback.data['vlc_player']:
				self.avs_playback.data['vlc_player'].stop()

	def stop(self):
		if self.avs_playback.data['vlc_player']:
			self.avs_playback.data['vlc_player'].stop()

	def resume(self): #TODO: Not implemented
		pass

	def is_playing(self):
		return self.avs_playback.data['is_playing']

	def getCurrentItem(self):
		return gstate.current_item

	def getCurrentToken(self):
		return gstate.current_token

	def getCurrentState(self):
		return gstate.current_state
