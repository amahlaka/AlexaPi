#alexa/helper/shared.py

import os
import time
import optparse
import tempfile

import RPi.GPIO as GPIO
from alexa.helper.colors import *
from alexa.helper.config import config
from alexa.helper.logger import logger_initialize
from alexa.helper.logger import logger
from alexa.player.player import MediaPlayer
from alexa.helper.thread import thread_manager

ROOT_DIR = os.path.dirname(os.path.abspath('./src'))
resources_path = os.path.join(ROOT_DIR, 'resources', '')
tmp_path = os.path.join(tempfile.mkdtemp(prefix='AlexaPi-runtime-'), '')

#Get config
if config and 'debug' in config and 'alexa' in config['debug']:
	if config['debug']['alexa']: debug = True

#Get arguments
parser = optparse.OptionParser()
parser.add_option('-s', '--silent',
                dest="silent",
                action="store_true",
                default=False,
                help="start without saying hello"
                )

parser.add_option('-l', '--logfile',
                dest="logfile",
                action="store_true",
                default=False,
                help="create log file in /var/log/Alexa.log"
                )

cmdopts, cmdargs = parser.parse_args()
silent = cmdopts.silent
logfile = cmdopts.logfile

#Intialize logging
logger_initialize(config, logfile)

#Intialize player
player = MediaPlayer(logger, bcolors)


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

class _Playback:
	def hello(self):
		player.play_local(resources_path+'hello.mp3')

	def yes(self):
		player.play_local(resources_path+'alexayes.mp3', 0)

	def halt(self):
		player.play_local(resources_path+'alexahalt.mp3')

	def beep(self):
		player.play_local(resources_path+'beep.wav', 100)

	def error(self):
		player.play_local(resources_path+'error.mp3')

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
playback = _Playback()
