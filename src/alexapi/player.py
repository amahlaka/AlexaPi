import vlc
import time
import threading
from collections import deque

from shared import *
import player_state as pstate

player = None
alexa_playback_progress_report_request = None
alexa_getnextitem = None
tuneinplaylist = None

queueplaying = False
queuepaused = False

class QueueManager(object):
	"""
	Build a queue of audio file for play sequencially
	"""
	q = deque()

	instance = None
	player = None


	def __init__(self):
		self.instance = vlc.Instance('--aout=alsa') # , '--alsa-audio-device=mono', '--file-logging', '--logfile=vlc-log.txt')


	def addItem(self, item):
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


	def queue_and_play(self, file, offset, overRideVolume):
		global queueplaying, queuepaused
		#TODO: add volumue override

		self.addItem(file)

		while True:
			if queueplaying is False and queuepaused is False:
				queueplaying = True
				queuepaused = False

				self.player = self.instance.media_player_new()
				media = self.instance.media_new(self.getNextItem())
				self.player.set_media(media)
				events = media.event_manager()
				events.event_attach(vlc.EventType.MediaStateChanged, self.queue_callback, self.player)

				if debug: print "{}Queue playing:{} {}".format(bcolors.OKBLUE, bcolors.ENDC, self.getCurrentItem())
				self.player.play()
				time.sleep(.1) # Allow time for state_callback to run


				# TODO: Probably need queue_callback state
				while queueplaying:
					time.sleep(.5) # Prevent 100% CPU untilzation
					continue

				#TODO: Do I still need this? 
				#queueplaying = False

			if self.getItemCount() == 0: # No more items in queue. Quit loop
				#TODO: Do stuff
				break

			time.sleep(1) # Prevent 100% CPU untilzation


	def stop(self):
		global queueplaying, queuepaused
		queueplaying = False
		queuepaused = False
		self.q.clear()
		self.player.stop()


	def is_playing(self):
		global queueplaying
		print "******** queueplaying: {}".format(queueplaying)
		return queueplaying


	def queue_callback(self, event, player):
		global queueplaying

		state = player.get_state()

		if debug: print("{}Queue Player State:{} {}".format(bcolors.OKGREEN, bcolors.ENDC, state))
		if state == 3:		#Playing
			queueplaying = True

		elif state == 5:	#Stopped
			queueplaying = False

		elif state == 6:	#Ended
			queueplaying = False
			pstate.audioplaying = False
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
			queueplaying = False


# Initialize queue manager
queue_manager = QueueManager()


def setup(playback_progress_report_request, getnextitem, tplaylist):
	global alexa_playback_progress_report_request, alexa_getnextitem, tuneinplaylist

	tuneinplaylist = tplaylist
	alexa_playback_progress_report_request=playback_progress_report_request
	alexa_getnextitem = getnextitem


def queue_and_play(file, offset=0, overRideVolume=0):
	queue_manager.queue_and_play(file, offset, overRideVolume)

def resume_queue():
	queue_manager.resume()

def pause_queue():
	queue_manager.pause()


def stop_queue():
	queue_manager.stop()

def is_queue_playing():
	return queue_manager.is_playing()


def is_queue_paused():
	return queue_manager.is_paused()


def play(file, offset=0, overRideVolume=0):
	global player

	if (file.find('radiotime.com') != -1):
		file = tuneinplaylist(file)

	if debug: print("{}Play_Audio Request for:{} {}".format(bcolors.OKBLUE, bcolors.ENDC, file))
	GPIO.output(config['raspberrypi']['plb_light'], GPIO.HIGH)

	instance = vlc.Instance('--aout=alsa') # , '--alsa-audio-device=mono', '--file-logging', '--logfile=vlc-log.txt')
	player = instance.media_player_new()
	media = instance.media_new(file)
	player.set_media(media)

	events = media.event_manager()
	events.event_attach(vlc.EventType.MediaStateChanged, state_callback, player)

	if (overRideVolume == 0):
		player.audio_set_volume(pstate.currVolume)
	else:
		player.audio_set_volume(overRideVolume)

	player.play()
	time.sleep(.1) # Allow time for state_callback to run

	while pstate.audioplaying:
		time.sleep(.1) # Prevent 100% CPU untilzation
		continue

	GPIO.output(config['raspberrypi']['plb_light'], GPIO.LOW)


def stop():
	global player
	print "Stopping..."
	player.stop()




def state_callback(event, player):
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
		pstate.audioplaying = True
		if pstate.streamid != "":
			rThread = threading.Thread(target=alexa_playback_progress_report_request, args=("STARTED", "PLAYING", pstate.streamid))
			rThread.start()

	elif state == 5:	#Stopped
		pstate.audioplaying = False
		if pstate.streamid != "":
			rThread = threading.Thread(target=alexa_playback_progress_report_request, args=("INTERRUPTED", "IDLE", pstate.streamid))
			rThread.start()
		pstate.streamurl = ""
		pstate.streamid = ""
		pstate.nav_token = ""

	elif state == 6:	#Ended
		pstate.audioplaying = False
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

	elif state == 7:
		pstate.audioplaying = False
		if pstate.streamid != "":
			rThread = threading.Thread(target=alexa_playback_progress_report_request, args=("ERROR", "IDLE", pstate.streamid))
			rThread.start()

		pstate.streamurl = ""
		pstate.streamid = ""
		pstate.nav_token = ""
