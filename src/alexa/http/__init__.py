#alexa/http/http.py

import sys
import json
import time
import random
import requests

from memcache import Client
from collections import deque
from hyper.contrib import HTTP20Adapter

import alexa

#sys.tracebacklimit = 0
avs_auth_url = alexa.config['alexa']['AuthUrl']
avs_base_url = alexa.config['alexa']['BaseUrl']
API_VERSION = alexa.config['alexa']['API_Version']
servers = ["127.0.0.1:11211"]

log = alexa.logger.getLogger(__name__)
mc = Client(servers, debug=1)
currentFuncName = sys._getframe().f_code.co_name


class res_type:
	BLANK	= 0
	DATA	= 1
	ERROR	= 2

class Http:

	class _Ping:
		def __init__(self, session):
			self._session = session
			self._stop = False
			self._interval = 60 * 5 # Five minutes
			#self._interval = 2 # Ten seconds for testing

		def ping(self):
			def exit(r):
				if r:
					r.close()

			def wait_interval():
				count = 0
				while count < self._interval:
					start_time = time.time()

					for number in range(8):
						time.sleep(.1)
						if self._stop:
							return True

					end_time = time.time()
					elapsed_time = 1 - (end_time - start_time)
					if elapsed_time > 0:
						time.sleep(1 - (end_time - start_time))
					count += 1

			while True:
				r = False
				if wait_interval():
					exit(r)
					return

				log.debug('')
				log.debug('Pinging AVS...')
				log.debug('')

				r = self._session.get('/ping')
				exit(r) #TODO: Do I need to close after every ping?

		def start(self, interval=False):
			if interval:
				self._interval = interval

			alexa.thread_manager.start(target=self.ping, stop=self.stop)

		def stop(self):
			self._stop = True

	class _Session:
		class _HttpQueue():

			def __init__(self):
				self._q = deque() #A Thread safe queue used to play audio files play sequencially (FIFO)
				self._item_count = 0

			def addItem(self, item):
				self._q.appendleft(item)
				self._item_count =  sum(1 for i in self._q)
				#log.debug("{}Add to http queue:{} {} | Count: {}".format(log.color.OKBLUE, log.color.ENDC, item, self._item_count))

			def pop(self):
				current_item = self._q.pop()
				self._item_count -= 1

			def getNextItem(self):
				if self._q:
					current_item = self._q[-1]
					return current_item
				else:
					return None

			def getItemCount(self):
				return self._item_count


		def __init__(self):
			#Initialize per: https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/docs/managing-an-http-2-connection#prerequisites
			#TODO: If the attempt to create a new connection fails, the client is expected to retry with an exponential back-off.

			self._max_retransmit_count = 3 #Global retry value

			self._auth_token = None
			self.is_authenticated = False
			self._http_queue = self._HttpQueue()
			self._error_callback = self._error_session_callback
			self._wait_for_http_response = False

			count = 0
			while not self._check_internet():
				count += 1
				alexa.led.blink_wait()
				time.sleep(self._back_off_wait(count))

			self._authenticate()
			self._http_session = self._initialize_new_http_session(avs_base_url)
			self._open_downchannel_stream()
			self._synchronize_state()

			alexa.led.blink_rdy()

		def _initialize_new_http_session(self, url):
			s = requests.Session()
			s.mount(url, HTTP20Adapter())
			return s

		def _check_internet(self):
			log.info("Checking Internet Connection...")
			try:
				self._initialize_new_http_session('https://api.amazon.com/auth/o2/token')
				log.info("Connection $OKOK$RESET")
				return True

			except Exception as e:
				log.debug("Connection $ERRORFailed$RESET - %s" % e)
				return False

		def _back_off_wait(self, n):
			wait_time = (2 ** n) + (random.randint(0, 1000) / 1000)
			log.info('Retrying in {} seconds'.format(wait_time))
			return wait_time

		def _authenticate(self, force=False):
			http_session = self._initialize_new_http_session(avs_auth_url)
			current_token = mc.get("access_token")
			refresh_token = alexa.config['alexa']['refresh_token']

			if (not current_token and refresh_token) or force:
				count = 0
				self.is_authenticated = False
				url_path = '%s/auth/o2/token' % avs_auth_url
				headers = {'Content-Type' : 'application/x-www-form-urlencoded', 'User-Agent': 'Alexa Python Agent'}
				payload = {"grant_type" : "refresh_token", "refresh_token" : refresh_token, "client_id" : alexa.config['alexa']['Client_ID'], "client_secret" : alexa.config['alexa']['Client_Secret'], }

				while not self.is_authenticated:
					count += 1

					response = http_session.post(url_path, headers=headers, data=payload, timeout=None) #TODO: Add error checking
					if response:
						j_resp = json.loads(response.text)

						log.debug('New token ({}) retrieved and expires in: {}'.format(j_resp['access_token'], j_resp['expires_in']))
						self._auth_token = j_resp['access_token']
						mc.set("access_token", j_resp['access_token'], j_resp['expires_in'] - 30)

						self.is_authenticated = True

					else:
						time.sleep(self._back_off_wait(count))

				return True

			elif current_token:
				self._auth_token = current_token
				self.is_authenticated = True
				return True

			elif not refresh_token:
				raise Exception("Config 'Refresh' not configured!!")

			return False

		def _open_downchannel_stream(self):
			response = False
			full_url = '{}/{}/directives'.format(avs_base_url, API_VERSION)
			headers = {"Authorization": "Bearer %s" % self._auth_token, 'User-Agent': 'Alexa Python Agent'}

			try:
				#response = self._initialize_new_http_session(avs_auth_url).get(full_url, headers=headers, stream=True, timeout=None)
				response = self._http_session.get(full_url, headers=headers, stream=True, timeout=None)

			except Exception as e:
				if response:
					response.close()

				log.exception("{}(): Could not open AVS downchannel stream - {}".format(currentFuncName, full_url))
				log.exception("error: %s" % e)
				return False

			return True

		def _synchronize_state(self):
			response = False
			full_url = '{}/{}/events'.format(avs_base_url, API_VERSION)
			headers = {"Authorization": "Bearer %s" % self._auth_token, 'User-Agent': 'Alexa Python Agent'}
			api = {"context": [],"event": {"header":{"namespace":"System","name":"SynchronizeState","messageId":"SyncState",},"payload": {}}}
			payload = {'file': json.dumps(api)}

			try:
				response = self._http_session.post(full_url, headers=headers, files=payload, stream=True, timeout=None)
				return response

			except Exception as e:
				if response:
					response.close()

				log.exception("{}(): Could not synchronize state - %s".format(currentFuncName, full_url))
				log.exception("error: %s" % e)

			return False

		def _response_check_callback(self, response): #Return value is processed by http_queue
			if response:
				http_code = response.status_code

				if http_code >= 200 and http_code < 300:
					if http_code == 204:
						#log.debug("Request Response is null $OK(This is OKAY!)$RESET")
						return [res_type.BLANK]

					return [res_type.DATA, response]

				if http_code == 403:
					response.close()
					return [res_type.ERROR]

			log.exception('{}Unknown response: {} {}'.format(log.color.FAIL, response, log.color.ENDC))
			alexa.led.blink_error()
			alexa.playback.error()

			return [res_type.ERROR]

		def _error_session_callback(self, exception):
			if 'errno' in exception:
				if exception.errno == 32: #Broken Pipe (Most likely invalid token. Get a new one
					log.exception('An http error has occurred!! - $BOLDerror #%$RESET', (exception.errno,))
					self._authenticate(True)

				elif exception.errno < 0: #TODO: A really bad requests error?
					log.exception('{}An http error has occurred!!{} - error #{}'.format(log.color.WARNING, log.color.ENDC, exception.errno))

			else:
				if exception == exceptions.AttributeError:
					log.execption('Applications error!')

				elif exception == StreamResetError:
					log.exception('{}Connection was forcefully closed by the remote server!!{}'.format(log.color.WARNING, log.color.ENDC))
					self._authenticate(True)

		def _post(self, path, payload=False):
			response = False
			full_url = avs_base_url + path
			headers = {"Authorization": "Bearer %s" % self._auth_token, 'User-Agent': 'Alexa Python Agent'}

			try:
				return self._response_check_callback(self._http_session.post(full_url, headers=headers, files=payload, stream=True, timeout=None))

			except Exception as e:
				if response:
					response.close()

				log.exception("{}(): Could not post to: {}".format(currentFuncName, full_url))
				log.exception("error: %s" % e)
				self._error_callback(e)

			return False

		def _get(self, path):
			response = False
			full_url = avs_base_url + path
			headers = {"Authorization": "Bearer %s" % self._auth_token, 'User-Agent': 'Alexa Python Agent'}

			try:
				return self._response_check_callback(self._http_session.get(full_url, headers=headers, stream=True, timeout=None))

			except Exception as e:
				if response:
					response.close()

				log.exception("{}(): Could not GET: {}".format(currentFuncName, full_url))
				log.exception("error: %s" % e)
				self._error_callback(e)

			return False

		def process_http_queue(self): #Sends a response to the decontructor for processing. Returning False ends the transmission
			count = 0
			while self._http_queue.getItemCount() > 0:
				if not self._wait_for_http_response:
					count += 1
					self._wait_for_http_response = False

					next_http_request = self._http_queue.getNextItem()

					if next_http_request[0] == 'post':
						#TODO: do something with msg_id later, e.g., next_http_request[1]
						path = next_http_request[2]
						payload = next_http_request[3]
						res_data = self._post(path, payload)

					elif next_http_request[0] == 'get':
						path = next_http_request[1]
						res_data = self._get(path)

					if res_data:
						if res_data[0] == res_type.DATA:# Has data - Return data which will be parsed by the interface manager
							self._wait_for_http_response = False
							self._http_queue.pop()
							#print res_data[1]
							return res_data[1]

						elif res_data[0] == res_type.BLANK: # Return False which will end the transmission
							self._wait_for_http_response = False
							self._http_queue.pop()
							return False

						elif res_data[0] == res_type.ERROR:
							pass

					if count > self._max_retransmit_count:
						self._wait_for_http_response = False
						self._http_queue.pop()
						log.debug('{}Reached max retries; Giving up!{}'.format(log.color.FAIL, log.color.ENDC))
						return False

				time.sleep(self._back_off_wait(count))

	def __init__(self):
		self._avs_http_session = self._Session()
		if self._avs_http_session.is_authenticated == True:
			self._ping = self._Ping(self)
			self._ping.start()

	def synchronizeState(self, state):
		log.debug(state)

	def post(self, msg_id, path, payload=False):
		http_item = ['post', msg_id, path, payload]
		self._avs_http_session._http_queue.addItem(http_item)
		return self._avs_http_session.process_http_queue()

	def get(self, path):
		http_item = ['get', path]
		self._avs_http_session._http_queue.addItem(http_item)
		return self._avs_http_session.process_http_queue()

	def close(self):
		self._ping.stop()
