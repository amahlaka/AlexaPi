import os
import uuid
import unittest

from alexa import alexa
from alexa.player.player import PlaybackDataContainer

log = alexa.logger(__name__)

class TestPlayer(unittest.TestCase):

	def _playerCallback(self, state):
		# Fake callback
		log.info('State: ' + str(state))
		if state == 8:
			log.info('Audio queue almost empty')

	def test_1_dynamic_variable(self):
		playback = PlaybackDataContainer(key='dd', test=1, david='roth')
		playback.data['message'] = 'hello'
		log.info(playback.data['message'])
		log.info(playback.data['key'])
		log.info(playback.data['test'])
		log.info(playback.data['david'])

		# Remove Items
		#self.assertEqual(playback.rm('dd'), None)
		#self.assertEqual(playback.clr(), None)

	def test_2_play_avs_response(self):
		for loop in range(0, 3):
			loop += 1

			token = 'fake_token1-loop({})-{}'.format(loop, uuid.uuid4())
			content = alexa.resources_path + "hello.mp3"
			alexa.player.package.add(token=token, content=content)
			alexa.thread_manager.start(alexa.player.play_avs_response, alexa.player.stop, token, self._playerCallback)

			token = 'fake_token2-loop({})-{}'.format(loop, uuid.uuid4())
			content = alexa.resources_path + "hello.mp3"
			alexa.player.package.add(token=token, content=content)
			alexa.thread_manager.start(alexa.player.play_avs_response, alexa.player.stop, token, self._playerCallback)

			token = 'fake_token3-loop({})-{}'.format(loop, uuid.uuid4())
			content = alexa.resources_path + "hello.mp3"
			alexa.player.package.add(token=token, content=content)
			alexa.thread_manager.start(alexa.player.play_avs_response, alexa.player.stop, token, self._playerCallback)

	def test_3_play_local(self):
		alexa.playback.beep()
		alexa.playback.hello()
		alexa.playback.halt()
		alexa.playback.error()

if __name__ == '__main__':
	unittest.main()
