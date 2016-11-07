import sys
import logging

class _RootLogger:
	def __init__(self, config, log_file):
		self._logger = logging.getLogger()

		# create a file handler
		if not log_file:
			handler = logging.StreamHandler(sys.stdout)
		else:
			handler = logging.FileHandler('/var/log/Alexa.log')

		# create a logging format
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		handler.setFormatter(formatter)

		# add the handlers to the logger
		self._logger.addHandler(handler)

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

def logger_initialize(configuration, log_file=False):
	_RootLogger(configuration, log_file) #Initialize logger

def logger(name):
	return logging.getLogger(name)
