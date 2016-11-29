import vlc

import alexa.thread_manager
from alexa.enum import Enum
from alexa import logger


log = logger.getLogger(__name__)

class Event(Enum): pass

Event({
	'Idle': 0,
	'Opening': 1,
	'Buffering': 2,
	'Playing': 3,
	'Paused': 4,
	'Stopped': 5,
	'Ended': 6,
	'Error': 7
})

class StateManager():
	def __init__(self):
		pass

	def _stop(self):
		print '<STUB> Stopping State Manager!!!'

	def callback(self, event, playback):

		def _callback(event, playback):
			queue = False
			vlc_state = playback.data['vlc_player'].get_state()

			if 'token' in playback.data:
				name = playback.data['token']
			else:
				name = playback.data['caller_name']

			if 'queue' in playback.data:
				queue = playback.data['queue']

			log.debug("{{ok}}Media Player State:{{ok}} %s/%s", vlc_state, name)

			#if playback.data['interface_callback'] is not None: #Do callback with VLC state msg
			#	playback.data['interface_callback'](gstate.current_state)

			if vlc_state == vlc.State.Playing:	#Playing
				playback.data['is_playing'] = True
				playback.data['is_paused'] = False

				if playback.data['interface_callback']:
					gstate.current_state = State.Playing
					#self.audio_player_interface.PlaybackStarted()

				if queue:
					if not queue.getItemCount() == 0 and 'queue_almost_empty' in playback.data and playback.data['queue_almost_empty'] and playback.data['interface_callback']: #Do callback with msg playback almost empty
						State = State.PlaybackNearlyFinished

			elif vlc_state == vlc.State.Paused:	#Paused
				playback.data['is_playing'] = False
				playback.data['is_paused'] = True

				if playback.data['interface_callback']:
					gstate.current_state = StateDiagram.PAUSED
					self.audio_player_interface.PlaybackPaused()

			elif vlc_state == vlc.State.Stopped:	#Stopped
				playback.data['is_playing'] = False

				if playback.data['interface_callback']:
					gstate.current_state = StateDiagram.STOPPED
					self.audio_player_interface.PlaybackStopped()

			elif vlc_state == vlc.State.Ended:	#Ended
				playback.data['is_playing'] = False

				#if playback.data['playback_type'] == 'remote' and self._queue.getItemCount() == 0:
				#	log.debug('Clearing...')
				#	self.package.clr()
				#	gstate.current_item = ''

			elif vlc_state == vlc.State.Error:	#Error
				playback.data['is_playing'] = False
				playback.data['is_paused'] = False

		alexa.thread_manager.start(_callback, self._stop, event, playback)
