import json
import time
import requests
import threading

from memcache import Client
from hyper.contrib import HTTP20Adapter


API_VERSION = 'v20160207'
avs_auth_url = 'https://api.amazon.com'
avs_base_url = 'https://avs-alexa-na.amazon.com'
servers = ["127.0.0.1:11211"]
mc = Client(servers, debug=1)

class API:
	__avs_session = False

	class __Session:
		__config = False
		__auth_token = None
		__session = None

		class __Ping:
			__session = None
			__stop = False
			__interval = 60 * 5 # Five minutes

			def __init__(self, session):
				self.__session = session

			def start(self, interval=False):
				if interval:
					self.__interval = interval

				timer = threading.Thread(target=self.ping)
				timer.start()

			def stop(self):
				self.__stop = True

			#def update(self, new_interval):
			def ping(self):
				count = 0

				while True:
					if count > 50:
						break

					if self.__stop:
						return

					time.sleep(0.1)
					count += 1

				while True:
					count = 0
					print "Pinging..."

					try:
						r = self.__session.get('/ping')

					except Exception as e:
						print "ping(): could not fetch %s" % path
						print "error: %s" % e

					while count < self.__interval:
						time.sleep(1)
						if self.__stop:
							return
						count += 1

		def __init__(self, config):
			# Initialize per: https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/docs/managing-an-http-2-connection#prerequisites
			self.__config = config
			self.__auth_token = self.__authenticate()
			self.__ping = self.__Ping(self)
			self.__session = self.__new_session(avs_base_url)
			self.__open_downchannel_stream()
			self.__synchronize_state(self.__ping)

		def __new_session(self, url):
			s = requests.Session()
			s.mount(url, HTTP20Adapter())
			return s

		def __authenticate(self):
			session = self.__new_session(avs_auth_url)
			current_token = mc.get("access_token")
			refresh_token = self.__config['alexa']['refresh_token']

			if not current_token and refresh_token:
				url_path = '%s/auth/o2/token' % avs_auth_url
				headers = {'Content-Type' : 'application/x-www-form-urlencoded'}
				payload = {"grant_type" : "refresh_token", "refresh_token" : refresh_token, "client_id" : self.__config['alexa']['Client_ID'], "client_secret" : self.__config['alexa']['Client_Secret'], }

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
				request = self.__session.get(full_url, headers=headers, stream=True, timeout=None)

			except Exception as e:
				print "__open_downchannel_stream(): Could not open AVS downchannel stream - %s" % full_url
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
				#print request.headers['x-amzn-requestid']

			except Exception as e:
				print "__synchronize_state(): Could not synchronize state - %s" % full_url
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

			try:
				request = self.__session.post(full_url, headers=headers, files=payload, stream=True, timeout=None)

			except Exception as e:
				print "synchronize_state(): could not fetch %s" % full_url
				print "error: %s" % e
				return False

			return request

		def get(self, path):
			full_url = avs_base_url + path
			headers = {"Authorization": "Bearer %s" % self.__auth_token}

			try:
				request = self.__session.get(full_url, headers=headers, stream=True, timeout=None)

			except Exception as e:
				print "synchronize_state(): could not fetch %s" % full_url
				print "error: %s" % e
				return False

			return request

	def __init__(self, config):
		self.__avs_session = self.__Session(config)

	def close(self):
		self.__avs_session.get_pinger().stop()

	def synchronize_state(self):
		path = '/{}/events'.format(API_VERSION)
		api = {"context": [],"event": {"header":{"namespace":"System","name":"SynchronizeState","messageId":"SyncState",},"payload": {}}}
		payload = {'file': json.dumps(api)}

		r = self.__avs_session.post(path, payload)
		print 'Status code: %s' % r.status_code
