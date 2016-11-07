#alexa/helper/shared.py

import os
import time
import optparse
import tempfile

import RPi.GPIO as GPIO
from alexa.helper.config import config
from alexa.helper.logger import logger_initialize
from alexa.helper.logger import logger

ROOT_DIR = os.path.dirname(os.path.abspath('./src'))
resources_path = os.path.join(ROOT_DIR, 'resources', '')
tmp_path = os.path.join(tempfile.mkdtemp(prefix='AlexaPi-runtime-'), '')

if config and 'debug' in config and 'alexa' in config['debug']:
	if config['debug']['alexa']: debug = True

#Intialize logging
logger_initialize(config)

#Get arguments
parser = optparse.OptionParser()
parser.add_option('-s', '--silent',
                dest="silent",
                action="store_true",
                default=False,
                help="start without saying hello"
                )

cmdopts, cmdargs = parser.parse_args()
silent = cmdopts.silent

class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

class _GPIO:
	def __init__(self):
		GPIO.setwarnings(False)
		GPIO.cleanup()
		GPIO.setmode(GPIO.BCM)

class Button:
	def __init__(self, callback):
		GPIO.setup(config['raspberrypi']['button'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(config['raspberrypi']['button'], GPIO.FALLING, callback=callback, bouncetime=100)

	def get_button_status(self):
		return GPIO.input(config['raspberrypi']['button'])

class _Led:
	def __init__(self):
		GPIO.setup(config['raspberrypi']['lights'], GPIO.OUT)
		GPIO.output(config['raspberrypi']['lights'], GPIO.LOW)

	def rec_on(self):
		GPIO.output(config['raspberrypi']['rec_light'], GPIO.HIGH)

	def rec_off(self):
		GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)

	def status_on(self):
		GPIO.output(config['raspberrypi']['plb_light'], GPIO.HIGH)

	def status_off(self):
		GPIO.output(config['raspberrypi']['plb_light'], GPIO.LOW)

	def blink_rdy(self):
		for x in range(0, 3):
			time.sleep(.1)
			GPIO.output(config['raspberrypi']['rec_light'], GPIO.HIGH)
			time.sleep(.1)
			GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)

	def blink_wait(self):
		for x in range(0, 1):
			time.sleep(1)
			GPIO.output(config['raspberrypi']['rec_light'], GPIO.HIGH)
			time.sleep(1)
			GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)

	def blink_valid_data_received(self):
		for x in range(0, 3):
			time.sleep(.2)
			GPIO.output(config['raspberrypi']['plb_light'], GPIO.HIGH)
			time.sleep(.2)
			GPIO.output(config['raspberrypi']['plb_light'], GPIO.LOW)

	def blink_error(self):
		for x in range(0, 3):
			time.sleep(.2)
			GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)
			GPIO.output(config['raspberrypi']['lights'], GPIO.HIGH)
			time.sleep(.2)
			GPIO.output(config['raspberrypi']['lights'], GPIO.LOW)
			GPIO.output(config['raspberrypi']['rec_light'], GPIO.HIGH)
			time.sleep(.2)
			GPIO.output(config['raspberrypi']['rec_light'], GPIO.LOW)
_GPIO()
led = _Led()
