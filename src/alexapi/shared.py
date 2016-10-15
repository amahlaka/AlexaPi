import yaml
import config
import optparse
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

with open(config.filename, 'r') as stream:
        config = yaml.load(stream)
