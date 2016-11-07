#alexapi/avs/directive_dispatcher.py

import json
import email

import alexa.helper.shared as shared
import alexa.player.player as player

log = shared.logger(__name__)

class DirectiveDispatcher:
	__interface_manager = None
	__payload = None

	def __init__(self, interface_manager):
		self.__interface_manager = interface_manager
		self.__payload =  interface_manager.Payload

	def find_attachement(self, payload, directive):
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
		if r and r.status_code == 200:
			data = "Content-Type: " + r.headers['content-type'] +'\r\n\r\n'+ r.content
			msg = email.message_from_string(data)

			for payload in msg.get_payload():
				if payload.get_content_type() == "application/json":
					j = json.loads(payload.get_payload())
					log.debug('')
					log.debug('')
					log.debug("{}->{}{}JSON String Received:{} {}".format(shared.bcolors.BOLD, shared.bcolors.ENDC, shared.bcolors.OKBLUE, shared.bcolors.ENDC, json.dumps(j)))
					log.debug('')
					log.debug('')

					binary = self.find_attachement(msg.get_payload(), j)
					if binary:
						filename = shared.tmp_path + binary.get('Content-ID').strip("<>")+".mp3"
						with open(filename, 'wb') as f:
							log.debug('')
							log.debug('Saving payload: %s' % filename)
							log.debug('')
							f.write(binary.get_payload())
					else:
						filename = False

					self.__payload.json = j
					self.__payload.filename = filename
					self.__interface_manager.dispatch_interface(self.__payload)

			return

		elif r and r.status_code == 204:
			shared.led.rec_off()
			shared.led.blink_error()
			log.debug("{}Request Response is null {}(This is OKAY!){}".format(shared.bcolors.OKBLUE, shared.bcolors.OKGREEN, shared.bcolors.ENDC))

		else:
			player.play_local(shared.resources_path+'error.mp3')
			log.debug("{}(process_response Error){} Status Code: {} - {}".format(shared.bcolors.WARNING, shared.bcolors.ENDC, r.status_code, r.text))
			r.close()

			shared.led.status_off()
			shared.led.blink_valid_data_received()
