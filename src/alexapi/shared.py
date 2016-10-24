import os
import time
import yaml
import config
import optparse
import tempfile

import RPi.GPIO as GPIO


class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'


#Get arguments
parser = optparse.OptionParser()
parser.add_option('-s', '--silent',
                dest="silent",
                action="store_true",
                default=False,
                help="start without saying hello"
                )
parser.add_option('-d', '--debug',
                dest="debug",
                action="store_true",
                default=False,
                help="display debug messages"
                )

cmdopts, cmdargs = parser.parse_args()
silent = cmdopts.silent
debug = cmdopts.debug

tmp_path = os.path.join(tempfile.mkdtemp(prefix='AlexaPi-runtime-'), '')

with open(config.filename, 'r') as stream:
        config = yaml.load(stream)


class __GPIO:
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

class __Led:
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
__GPIO()
led = __Led()
