#alexa/logger/__init__.py

import sys
import logging
import traceback

from alexa.logger.terminal import *
from alexa.logger.simple_logger_markdown import Markdown

class _AlexaCustomLogger:
	class ColorFormatter(logging.Formatter):
		def __init__(self, use_color=False):
			self.markdown_formatter = Markdown.Formatter(use_color)
			logging.Formatter.__init__(self, self.markdown_formatter.log_format)

		def format(self, record):
			modified_record, self._fmt = self.markdown_formatter.format(record, self._fmt)
			return logging.Formatter.format(self, modified_record)

	def __init__(self):
		self._logger = logging.getLogger()
		self._logger.setLevel(logging.DEBUG)
		self._handler = logging.StreamHandler(sys.stdout)
		self._handler.setFormatter(self.ColorFormatter())
		self._logger.addHandler(self._handler)

	def setup(self, config, enable_file_logging):
		# clear current handlers
		for hdlr in self._logger.handlers[:]:  # remove all old handlers
			self._logger.removeHandler(hdlr)

		#if 'debug' in config:
		if enable_file_logging:
			if 'logFileLocation' in config['debug']:
				log_file_location =  config['debug']['logFileLocation']
			else:
				log_file_location = '/var/log/Alexa.log'

			# create a file handler
			handler = logging.FileHandler(log_file_location)
			print 'File logging {}enabled{}: Logging to {}{}{}'.format(FORMATS.BOLD, ESC_SEQ.RESET, FORMAT.ITALICS, log_file_location, ESC_SEQ.RESET)

		else:
			handler = logging.StreamHandler(sys.stdout)

		self._set_logging(config, handler)

	def _set_logging(self, config, handler):
		if config and 'debug' in config:
			if 'alexa' in config['debug']:
				self._logger.setLevel(self._get_debug_level(config['debug']['alexa']))

			if 'hpack' in config['debug']:
				hpack_logger = logging.getLogger('hpack')
				hpack_logger.setLevel(self._get_debug_level(config['debug']['hpack']))

			else:
				hpack_logger = logging.getLogger('hpack')
				hpack_logger.setLevel(logging.CRITICAL)

			if 'hyper' in config['debug']:
				hyper_logger = logging.getLogger('hyper')
				hyper_logger.setLevel(self._get_debug_level(config['debug']['hyper']))
			else:
				hyper_logger = logging.getLogger('hyper')
				hyper_logger.setLevel(logging.CRITICAL)

			if 'requests' in config['debug']:
				hyper_logger = logging.getLogger('requests')
				hyper_logger.setLevel(self._get_debug_level(config['debug']['requests']))
			else:
				hyper_logger = logging.getLogger('requests')
				hyper_logger.setLevel(logging.CRITICAL)

			if 'colorize' in config['debug']:
				colorize = config['debug']['colorize']
				if colorize:
					handler.setFormatter(self.ColorFormatter(True))
				else:
					handler.setFormatter(self.ColorFormatter())

		self._logger.addHandler(handler)

	def _get_debug_level(self, name):
		'''
		Level	Numeric value
		CRITICAL	50
		ERROR		40
		WARNING		30
		INFO		20
		DEBUG		10
		'''
		if name == 'critical':
			return logging.CRITICAL

		elif name == 'ERROR':
			return logging.ERROR

		elif name == 'warning':
			return logging.WARNING

		elif name == 'info':
			return logging.INFO

		elif name == 'debug':
			return logging.DEBUG

	def getLogger(self, name):
		log = logging.getLogger(name)
		Markdown.log_hooks(log) # add log.start() and log.blank_line() methods

		def exception_hook(exc_type, exc_value, exc_traceback):
			log.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

		sys.excepthook = exception_hook

		return log

_logger = _AlexaCustomLogger() #Initialize logger

def setup(configuration, enable_file_logging):
	_logger.setup(configuration, enable_file_logging)

def getLogger(name):
	return _logger.getLogger(name)
