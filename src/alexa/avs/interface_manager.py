#alexapi/avs/interface_manager.py

import os
import threading

import alexa.helper.shared as shared
from alexa.avs.directive_dispatcher import DirectiveDispatcher
from alexa.http.http import Http

MODULE_ROOT = 'alexa.avs'
INTERFACE_DIR = 'interface'

log = shared.logger(__name__)

class InterfaceManager:
	__directive_path = None
	__avs_session = None
	__directive_dispatcher = None

	class Payload:
		filename = None
		json = None

	def __init__(self):
		self.__directive_dispatcher = DirectiveDispatcher(self) #Initialize dispather before Http()
		self.__avs_session = Http(self) #TODO: Implement http callback
		self.__import_modules()

	def __check_if_not_error(self, response):
		if not response.status_code >= 200 and not response.status_code < 300:
			log.debug('')
			log.debug('{}(process_response Error){} Status Code: {} - {}'.format(shared.bcolors.WARNING, shared.bcolors.ENDC, response.status_code, response.text))
			log.debug('')
			return False

		return True

	def __import_modules(self):
		log.info('')
		log.info('----------------------')
		for module in os.listdir(os.path.dirname(__file__) + '/%s/' % INTERFACE_DIR):
			if module == '__init__.py' or module[-3:] != '.py':
				continue

			module = '{}.{}.{}'.format(MODULE_ROOT, INTERFACE_DIR, module.strip('.py'))
			log.info('Importing ' + module + '...')
			__import__(module, locals(), globals())

		log.info('----------------------')
		log.info('')

		del module
		import interface #TODO: make dynamic

		for module in [x for x in dir(locals()[INTERFACE_DIR]) if not x.startswith('__') and not x == 'os']:
			mod = getattr(interface, module, False) #TODO: Make dynamic
			interface_ref = getattr(mod, module, False)(self)
			setattr(self, module, interface_ref)

	def get_avs_session(self):
		return self.__avs_session.get_avs_session()

	def send_event(self, namespace, event_name):
		class_instance = getattr(self, str(namespace), None)
		if class_instance:
			event_method = getattr(class_instance, str(event_name), None)
			if event_method:
				log.info('')
				log.info('')
				log.info('{}{}Dispatching event(namespace/name):{} {}/{}...'.format(shared.bcolors.BOLD, shared.bcolors.OKBLUE, shared.bcolors.ENDC, namespace, event_name))
				log.info('')
				gThread = threading.Thread(target=self.__directive_dispatcher.processor, args=(event_method(),))
				gThread.start()
				return

		log.info('')
		log.info('')
		log.info('{}Unknown event(namespace/name):{} {}/{}'.format(shared.bcolors.FAIL, shared.bcolors.ENDC, namespace, event_name))
		log.info('')

	def dispatch_interface(self, payload=False):
		namespace = payload.json['directive']['header']['namespace']
		directive_name = payload.json['directive']['header']['name']

		class_instance = getattr(self, str(namespace), None)

		if class_instance:
			directive_method = getattr(class_instance, str(directive_name), False)
			if directive_method:
				log.info('')
				log.info('')
				log.info('{}{}Dispatching directive(namespace/name):{} {}/{}...'.format(shared.bcolors.BOLD, shared.bcolors.OKBLUE, shared.bcolors.ENDC, namespace, directive_name))
				log.info('')
				gThread = threading.Thread(target=directive_method, args=(payload,))
				gThread.start()
				return

		log.info('')
		log.info('')
		log.info('{}Unknown directive(namespace/name):{} {}/{}'.format(shared.bcolors.FAIL, shared.bcolors.ENDC, namespace, directive_name))
		log.info('')

	def process_response(self, response):
		gThread = threading.Thread(target=self.__directive_dispatcher.processor, args=(response,))
		gThread.start()
