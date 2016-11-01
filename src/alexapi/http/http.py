#alexapi/http/http.py

import sys
import json
import time
import requests
import threading

from memcache import Client
from hyper.contrib import HTTP20Adapter

import alexapi.shared as shared
from helper.thread import thread_manager


avs_auth_url = shared.config['alexa']['AuthUrl']
avs_base_url = shared.config['alexa']['BaseUrl']
API_VERSION = shared.config['alexa']['API_Version']
servers = ["127.0.0.1:11211"]
mc = Client(servers, debug=1)
currentFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name #TODO: Add to debug class

class Http:
	__avs_session = False
	__interface = None

	class __Session:
		__interface = None
		__auth_token = None
		__session = None

		class __Ping:
			__initialized = False
			__session = None
			__stop = False
			__interval = 60 * 5 # Five minutes

			def __init__(self, session):
				try:
					self.__session = session
					self.__initialized = True

				except (KeyboardInterrupt, SystemExit):
					print 'Exiting...'
					if self.__initialized: self.stop()

			def ping(self):
				def pause():
					count = 0
					while count < self.__interval:
						start_time = time.time()

						for number in range(8):
							time.sleep(.1)
							if self.__stop:
								return True

						end_time = time.time()
						elapsed_time = 1 - (end_time - start_time)
						if elapsed_time > 0:
							time.sleep(1 - (end_time - start_time))
						count += 1

				while True:
					try:
						r = False
						if pause():
							return
						print
						print 'Pinging AVS...'
						print
						r = self.__session.get('/ping')

					except Exception as e:
						print "ping(): could not ping - response: %s" % r
						print "error: %s" % e

			def start(self, interval=False):
				if interval:
					self.__interval = interval

				thread_manager.start(self.ping, self.stop)

			def stop(self):
				self.__stop = True

		def __init__(self, interface):
			# Initialize per: https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/docs/managing-an-http-2-connection#prerequisites
			while not self.__check_internet():
				print(".")
				shared.led.blink_wait()

			self.__interface = interface
			self.__auth_token = self.__authenticate()
			self.__ping = self.__Ping(self)
			self.__session = self.__new_session(avs_base_url)
			self.__open_downchannel_stream()
			self.__synchronize_state(self.__ping)
			shared.led.blink_rdy()

		def __new_session(self, url):
			s = requests.Session()
			s.mount(url, HTTP20Adapter())
			return s

		def __check_internet(self):
			print("Checking Internet Connection...")
			try:
				self.__new_session('https://api.amazon.com/auth/o2/token')
				print("Connection {}OK{}".format(shared.bcolors.OKGREEN, shared.bcolors.ENDC))
				return True
			except:
				print("Connection {}Failed{}".format(shared.bcolors.WARNING, shared.bcolors.ENDC))
				return False

		def __authenticate(self):
			session = self.__new_session(avs_auth_url)
			current_token = mc.get("access_token")
			refresh_token = shared.config['alexa']['refresh_token']

			if not current_token and refresh_token:
				url_path = '%s/auth/o2/token' % avs_auth_url
				headers = {'Content-Type' : 'application/x-www-form-urlencoded'}
				payload = {"grant_type" : "refresh_token", "refresh_token" : refresh_token, "client_id" : shared.config['alexa']['Client_ID'], "client_secret" : shared.config['alexa']['Client_Secret'], }

				r = session.post(url_path, headers=headers, data=payload, timeout=None)
				resp = json.loads(r.text)
				mc.set("access_token", resp['access_token'], resp['expires_in'] - 30)

				self.__auth_token = resp['access_token']
				return self.__auth_token

			elif current_token:
				return current_token

			else:
				print "refresh not configured!" #TODO: Change to debug warning

		def __open_downchannel_stream(self):
			full_url = '{}/{}/directives'.format(avs_base_url, API_VERSION)
			headers = {"Authorization": "Bearer %s" % self.__auth_token}

			try:
				response = self.__session.get(full_url, headers=headers, stream=True, timeout=None)

			except Exception as e:
				print "{}(): Could not open AVS downchannel stream - {}".format(currentFuncName, full_url)
				print "error: %s" % e
				return False

			return True

		def __synchronize_state(self, ping):
			full_url = '{}/{}/events'.format(avs_base_url, API_VERSION)
			headers = {"Authorization": "Bearer %s" % self.__auth_token}
			api = {"context": [],"event": {"header":{"namespace":"System","name":"SynchronizeState","messageId":"SyncState",},"payload": {}}}
			payload = {'file': json.dumps(api)}

			def get_current_session(self):
				return self.__session
			try:
				request = self.__session.post(full_url, headers=headers, files=payload, stream=True, timeout=None)

			except Exception as e:
				print "{}(): Could not synchronize state - %s".format(currentFuncName, full_url)
				print "error: %s" % e
				return False

			ping.start()
			return True

		def get_pinger(self):
			return self.__ping

		def get_auth_token(self):
			return self.__auth_token

		def post(self, path, payload=False):
			full_url = avs_base_url + path
			headers = {"Authorization": "Bearer %s" % self.__auth_token}

			if shared.debug: print("\n{}<-{}{}JSON String Sent:{} {}".format(shared.bcolors.BOLD, shared.bcolors.ENDC, shared.bcolors.OKBLUE, shared.bcolors.ENDC, payload[0][1][1]))

			try:
				request = self.__session.post(full_url, headers=headers, files=payload, stream=True, timeout=None)

			except Exception as e:
				print "{}(): Could not post to: {}".format(currentFuncName, full_url)
				print "error: %s" % e
				return False

			return request

		def get(self, path):
			full_url = avs_base_url + path
			headers = {"Authorization": "Bearer %s" % self.__auth_token}

			try:
				request = self.__session.get(full_url, headers=headers, stream=True, timeout=None)

			except Exception as e:
				print "{}(): Could not get to: {}".format(currentFuncName, full_url)
				print "error: %s" % e
				return False

			return request

	def __init__(self, interface):
		self.__interface = interface
		self.__avs_session = self.__Session(interface)

	def get_avs_session(self):
		return self.__avs_session

	def close(self):
		self.__avs_session.get_pinger().stop()
