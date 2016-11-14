from alexa.thread import thread_manager

class StateManager():
	def __init__(self):
		pass

	def callback(self):
		def _callback(event, playback):
			vlc_state = playback.data['vlc_player'].get_state()

			if 'token' in playback.data:
				name = playback.data['token']
			else:
				name = playback.data['caller_name']

			log.debug("{}Media Player State:{} {}/{}".format(bcolors.OKGREEN, bcolors.ENDC, vlc_state, name))

			#if playback.data['interface_callback'] is not None: #Do callback with VLC state msg
			#	playback.data['interface_callback'](gstate.current_state)

			if vlc_state == vlc.State.Playing:	#Playing
				playback.data['is_playing'] = True
				playback.data['is_paused'] = False

				if playback.data['interface_callback']:
					gstate.current_state = StateDiagram.PLAYING
					self.audio_player_interface.PlaybackStarted()

				if not self._queue.getItemCount() == 0 and 'queue_almost_empty' in playback.data and playback.data['queue_almost_empty'] and playback.data['interface_callback']: #Do callback with msg playback almost empty
					self.audio_player_interface.PlaybackNearlyFinished()
					#playback.data['interface_callback'](8)

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

		thread_manager.start(_callback, self.stop, event, playback)
