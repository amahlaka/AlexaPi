#alexa/avs/interface_manager.py

import os
import time
import json
import email
import threading

from alexa import alexa
from alexa.http.http import Http

MODULE_ROOT = 'alexa.avs'
INTERFACE_DIR = 'interface'

log = alexa.logger(__name__)

class InterfaceManager:
	class Payload:
		filename = None
		json = None

	class DirectiveDeconsturtor:

		def __init__(self, interface_manager):
			self._interface_manager = interface_manager
			self._payload = interface_manager.Payload

		def _find_attachement(self, payload, directive):
			def get_attachement(url):
				for msg in payload:
					if msg.get_content_type() == "application/octet-stream":
						content_id = msg.get('Content-ID').strip("<>")
						if content_id == url.lstrip('cid:'):
							return msg

			if 'format' in directive['directive']['payload'] and directive['directive']['payload']['format'] == 'AUDIO_MPEG':
				return get_attachement(directive['directive']['payload'] and directive['directive']['payload']['url'])

			elif 'audioItem' in directive['directive']['payload']:
				if 'streamFormat' in directive['directive']['payload']['audioItem']['stream'] and directive['directive']['payload']['audioItem']['stream']['streamFormat'] == 'AUDIO_MPEG':
					return get_attachement(directive['directive']['payload']['audioItem']['stream']['url'])

			return False

		def processor(self, r):
			alexa.led.blink_valid_data_received()
			data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
			msg = email.message_from_string(data)

			for payload in msg.get_payload():
				log.debug('Processing payload')
				if payload.get_content_type() == "application/json":
					j = json.loads(payload.get_payload())
					log.debug('')
					log.debug('')
					log.debug("{}->{}{}JSON String Received:{} {}".format(alexa.bcolors.BOLD, alexa.bcolors.ENDC, alexa.bcolors.OKBLUE, alexa.bcolors.ENDC, json.dumps(j)))
					log.debug('')
					log.debug('')

					binary = self._find_attachement(msg.get_payload(), j)
					if binary:
						filename = alexa.tmp_path + binary.get('Content-ID').strip("<>")+".mp3"
						with open(filename, 'wb') as f:
							log.debug('')
							log.debug('Saving media attachement: %s' % filename)
							log.debug('')
							f.write(binary.get_payload())
					else:
						filename = False

					self._payload.json = j
					self._payload.filename = filename
					self._interface_manager.process_directive(self._payload)
					time.sleep(.2) #Need a pause to prevent audio race condition

			#if r: #TODO: Do I still need? Moving all connection handling to http module
			#	r.close()

	def __init__(self):
		self._synchronize_state = []
		self._directive_deconstructor = self.DirectiveDeconsturtor(self) #Initialize dispather before Http()
		self._avs_session = Http()
		self._import_modules()

	def _import_modules(self):
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

		for module in [x for x in dir(locals()[INTERFACE_DIR]) if not x.startswith('_') and not x == 'os']:
			mod = getattr(interface, module, False) #TODO: Make dynamic
			interface_ref = getattr(mod, module, False)(self)
			self._synchronize_state.append(interface_ref.initialState()) #Load default state
			setattr(self, module, interface_ref)

		self._avs_session.synchronizeState(self._synchronize_state)

	def get_avs_session(self):
		return self._avs_session.get_avs_session()

	def process_directive(self, payload=False): #Process directive received from AVS
		namespace = payload.json['directive']['header']['namespace']
		directive_name = payload.json['directive']['header']['name']

		class_instance = getattr(self, str(namespace), None)

		if class_instance:
			directive_method = getattr(class_instance, str(directive_name), False)
			if directive_method:
				log.info('')
				log.info('')
				log.info('{}{}Dispatching directive(namespace/name):{} {}/{}...'.format(alexa.bcolors.BOLD, alexa.bcolors.OKBLUE, alexa.bcolors.ENDC, namespace, directive_name))
				log.info('')
				gThread = threading.Thread(target=directive_method, args=(payload,))
				gThread.start()
				return

		log.info('')
		log.info('')
		log.info('{}Unknown directive(namespace/name):{} {}/{}'.format(alexa.bcolors.FAIL, alexa.bcolors.ENDC, namespace, directive_name))
		log.info('')

	def send_event(self, msg_id, path, payload): #Events as sent by an AVS Interface
		log.debug('')
		log.debug('')
		log.debug("{}<-{}{}JSON String Sent:{} {}".format(alexa.bcolors.BOLD, alexa.bcolors.ENDC, alexa.bcolors.OKBLUE, alexa.bcolors.ENDC, payload[0][1][1]))
		log.debug('')
		log.debug('')

		response = self._avs_session.post(msg_id, path, payload)

		if response:
			gThread = threading.Thread(target=self._directive_deconstructor.processor, args=(response,))
			gThread.start()

	def trigger_event(self, namespace, event_name): #Only used by main.py to send a speech event to AVS
		class_instance = getattr(self, str(namespace), None)
		if class_instance:
			event_method = getattr(class_instance, str(event_name), None)
			if event_method:
				log.info('')
				log.info('')
				log.info('{}{}Dispatching event(namespace/name):{} {}/{}...'.format(alexa.bcolors.BOLD, alexa.bcolors.OKBLUE, alexa.bcolors.ENDC, namespace, event_name))
				log.info('')
				response = event_method()

				if response:
					gThread = threading.Thread(target=self._directive_deconstructor.processor, args=(response,))
					gThread.start()

				return

		log.info('')
		log.info('')
		log.info('{}Unknown event(namespace/name):{} {}/{}'.format(alexa.bcolors.FAIL, alexa.bcolors.ENDC, namespace, event_name))
		log.info('')
