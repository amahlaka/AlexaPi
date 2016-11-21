import os
import unittest

import alexa
from alexa.logger.terminal import ATTRIBUTES

log = alexa.logger.getLogger(__name__)

class TestLogging(unittest.TestCase):

	# Need a way to combine two items: color and style
	def test_1_color_logger(self):
		print '%sTESTING%s' % (ATTRIBUTES.OK.BOLD, ATTRIBUTES.RESET)
		print '%sTESTING%s' % (ATTRIBUTES.OK.UNDERLINE.RED, ATTRIBUTES.RESET)
		print '%sTESTING%s' % (ATTRIBUTES.WHITE.BOLD.UNDERLINE.YELLOW, ATTRIBUTES.RESET)
		print '%sTESTING%s' % (ATTRIBUTES.BLUE.UNDERLINE.BOLD.RED, ATTRIBUTES.RESET)
		print '***********'


if __name__ == '__main__':
	unittest.main()
