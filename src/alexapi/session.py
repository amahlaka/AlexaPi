import requests
import json

from memcache import Client
from hyper.contrib import HTTP20Adapter


servers = ["127.0.0.1:11211"]
mc = Client(servers, debug=1)

class http2_connection:
	__API_VERSION = 'v20160207'
	__avs_auth_url = 'https://api.amazon.com'
	__avs_base_url = 'https://avs-alexa-na.amazon.com'
	__auth_token = False
	__session = False
	__config = False

	def __init__(self, config):
		self.__config = config
		self.authentication()
		self.__session = self.new_connection(self.__avs_base_url)
		self.downchannel_stream(self.__session, self.__avs_base_url)
		self.synchronize_state(self.__session, self.__avs_base_url)
		self.ping(self.__session, self.__avs_base_url)

	def __new__(cls):
		return self.__session

	def new_connection(self, url):
		s = requests.Session()
		s.mount(url, HTTP20Adapter())
		return s

	def get_base_url(self):
		return self.avs_base_url + '%s' % self.API_VERSION

	def authentication(self):
		self.__auth_token = mc.get("access_token")
		refresh = self.__config['alexa']['refresh_token']

		session = self.new_connection(self.__avs_auth_url)

		if not self.__auth_token and refresh:
			url_path = '%s/auth/o2/token' % self.__avs_auth_url
			headers = {'Content-Type' : 'application/x-www-form-urlencoded'}
			payload = {"grant_type" : "refresh_token", "refresh_token" : refresh, "client_id" : self.__config['alexa']['Client_ID'], "client_secret" : self.__config['alexa']['Client_Secret'], }

			r = session.post(url_path, headers=headers, data=payload, timeout=None)
			resp = json.loads(r.text)
			mc.set("access_token", resp['access_token'], resp['expires_in'] - 30)
			self.__auth_token = resp['access_token']

	def get_auth_token(self):
		return self.__auth_token

	def downchannel_stream(self, session, url):
		url_path = '{}/{}/directives'.format(url, self.__API_VERSION)
		headers = {"Authorization": "Bearer %s" % self.__auth_token}

		try:
			r = session.get(url_path, headers=headers, stream=True, timeout=None)
			print r.status_code

		except Exception as e:
			print "downchannel_stream(): could not fetch %s" % url_path
			print "error: %s" % e

	def synchronize_state(self, session, url):
		url_path = '{}/{}/events'.format(url, self.__API_VERSION)
		headers = {"Authorization": "Bearer %s" % self.__auth_token}
		payload = {"context": [],"event": {"header":{"namespace":"System","name":"SynchronizeState","messageId":"SyncState",},"payload": {}}}
		files = {'file': json.dumps(payload)}

		try:
			r = session.post(url_path, headers=headers, files=files, stream=True, timeout=None)
			print r.status_code

		except Exception as e:
			print "synchronize_state(): could not fetch %s" % url
			print "error: %s" % e

	def ping(self, session, url):
		url_path = '{}/ping'.format(url)
		headers = {"Authorization": "Bearer %s" % self.__auth_token}

		try:
			r = session.get(url_path, headers=headers, stream=True, timeout=None)
			print r.status_code

		except Exception as e:
			print "downchannel_stream(): could not fetch %s" % url_path
			print "error: %s" % e

		#print resp.headers['x-amzn-requestid'][0]


