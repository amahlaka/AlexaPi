import vlc
import ctypes

import alexa.thread_manager
from alexa import logger


log = logger.getLogger(__name__)

class _Enum(ctypes.c_uint):
	_enum_names_ = {}

	def __str__(self):
		n = self._enum_names_.get(self.value, '') or ('FIXME_(%r)' % (self.value,))
		return '.'.join((self.__class__.__name__, n))

	def __hash__(self):
		return self.value

	def __repr__(self):
		return '.'.join((self.__class__.__module__, self.__str__()))

	def __eq__(self, other):
		return ( (isinstance(other, _Enum) and self.value == other.value) or (isinstance(other, _Ints) and self.value == other) )

	def __ne__(self, other):
		return not self.__eq__(other)

class Event(_Enum):
	_enum_names_ = {
		0: 'NothingSpecial',
		1: 'Opening',
		2: 'Buffering',
		3: 'Playing',
		4: 'Paused',
		5: 'Stopped',
		6: 'Ended',
		7: 'Error',
	}

Event.Idle			= Event(0)
Event.BufferUnderun		= Event(1)
Event.Playing			= Event(2)
Event.PlaybackNearlyFinished	= Event(3)
Event.Finished			= Event(4)

Event.Paused			= Event(5)
Event.Stopped			= Event(6)
Event.Error			= Event(7)

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
