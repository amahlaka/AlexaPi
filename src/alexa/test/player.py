import os
import uuid
import unittest
import threading

import alexa.helper.shared as shared
from alexa.player.player import player
from alexa.player.player import _DynamicVariable as dynamic_var
from alexa.player.player import PlaybackDataContainer

log = shared.logger(__name__)

class TestPlayer(unittest.TestCase):

	def _playerCallback(self):
		# Fake callback
		plog.inf('** Player callback called!!')

	def test_1_dynamic_variable(self):
		playback = PlaybackDataContainer(key='dd', test=1, david='roth')
		playback.data['message'] = 'hello'
		log.info(playback.data['message'])
		log.info(playback.data['key'])
		log.info(playback.data['test'])
		log.info(playback.data['david'])

		ds = dynamic_var(True)
		#Add items
		self.assertEqual(ds.add(key='dd', test=1, david='roth'), None)

		#Retrieve items
		self.assertEqual(ds.get('key'), 'dd')
		self.assertEqual(ds.get('test'), 1)
		self.assertEqual(ds.get('david'), 'roth')

		# Remove Items
		self.assertEqual(ds.rm('key'), None)
		self.assertEqual(ds.rm('test'), None)
		self.assertEqual(ds.clr(), None)

		ds = dynamic_var()
		self.assertEqual(ds.add(key='dd', test=1, david='roth'), None)
		self.assertEqual(ds.get('dd', 'david'), 'roth')
		self.assertEqual(ds.get('dd', 'test'), 1)

		# Remove Items
		#self.assertEqual(ds.rm('dd'), None)
		#self.assertEqual(ds.clr(), None)

	def test_2_play_avs_response(self):
		for loop in range(0, 3):
			loop += 1

			token = 'fake_token1-loop({})-{}'.format(loop, uuid.uuid4())
			content = shared.resources_path + "hello.mp3"
			player.package.add(token=token, content=content)
			gThread = threading.Thread(target=player.play_avs_response, args=(token, self._playerCallback,))
			gThread.start()

			token = 'fake_token2-loop({})-{}'.format(loop, uuid.uuid4())
			content = shared.resources_path + "hello.mp3"
			player.package.add(token=token, content=content)
			gThread = threading.Thread(target=player.play_avs_response, args=(token, self._playerCallback,))
			gThread.start()

			token = 'fake_token3-loop({})-{}'.format(loop, uuid.uuid4())
			content = shared.resources_path + "hello.mp3"
			player.package.add(token=token, content=content)
			gThread = threading.Thread(target=player.play_avs_response, args=(token, self._playerCallback,))
			gThread.start()

	def test_3_play_local(self):
		player.play_local(shared.resources_path+"start.mp3")

if __name__ == '__main__':
	unittest.main()
