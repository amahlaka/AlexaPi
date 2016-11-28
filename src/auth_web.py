#! /usr/bin/env python

import os
import sys
import yaml
import json
import urllib
import socket
import logging
import cherrypy
import requests
import platform
import traceback

import alexapi.config

with open(alexapi.config.filename, 'r') as stream:
	config = yaml.load(stream)

DEBUG = True
PORT = 5050
FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'

logging.basicConfig(format=FORMAT)
log = logging.getLogger('cherrypy')
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
log.addHandler(handler)

if DEBUG:
    cherrypy.log.error_log.propagate = True
    cherrypy.log.access_log.propagate = True


class Start(object):

	def index(self):
                try:
			self.verify_config()

			sd = json.dumps({
				"alexa:all": {
					"productID": config['alexa']['Device_Type_ID'],
					"productInstanceAttributes": {
						"deviceSerialNumber": "001"
					}
				}
			})

			url = "https://www.amazon.com/ap/oa"
			callback = cherrypy.url() + "code"
			payload = {
				"client_id": config['alexa']['Client_ID'],
				"scope": "alexa:all",
				"scope_data": sd,
				"response_type": "code",
				"redirect_uri": callback
			}
		except Exception as e:
			return self.catch_error(e)

		req = requests.Request('GET', url, params=payload)
		prepared_req = req.prepare()
		raise cherrypy.HTTPRedirect(prepared_req.url)

	def code(self, var=None, **params):		# pylint: disable=unused-argument
		try:
			code = urllib.quote(cherrypy.request.params['code'])
			callback = cherrypy.url()
			payload = {
				"client_id": config['alexa']['Client_ID'],
				"client_secret": config['alexa']['Client_Secret'],
				"code": code,
				"grant_type": "authorization_code",
				"redirect_uri": callback
			}
			url = "https://api.amazon.com/auth/o2/token"

			response = requests.post(url, data=payload)
			resp = response.json()

			alexapi.config.set_variable(['alexa', 'refresh_token'], resp['refresh_token'])

			return (
				"<h2>Success!</h2><h3> Refresh token has been added to your "
				"config file, you may now reboot the Pi </h3><br>{}"
			).format(resp['refresh_token'])

		except Exception as e:
			return self.catch_error(e)

	def verify_config(self):
		skip = False
		error_detected = False
		errors = []
		alexa_params = ['Client_ID', 'Client_Secret', 'Device_Type_ID']

		if not 'alexa' in config:
			raise Exception("Configuration not valid")

		ca = config['alexa']

		for param in alexa_params:
			if not param in ca:
				errors.append("Missing %s configuration!" % param)
				skip = True
				error_detected = True

			if not skip and ca[param] == None:
				errors.append("Empty %s configuration!" % param)
				skip = True
				error_detected = True

			skip = False

		if error_detected:
			error_message = "Please fix the config.yaml file!\n" + " and ".join(errors)
			log.exception(error_message)
			raise Exception("Please fix the config.yaml file!\n" + "<br>\n".join(errors))


	def catch_error(self, e):
		log.exception('\n\n' + e.message + '\n\n')
		exc_type, exc_value, exc_traceback = sys.exc_info()
		lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
		print lines
		first_line = lines[0]
		lines.pop(0)
		return "<h2>INTERNAL ERROR!</h2><h3> An internal error occured! Error message: </h3><br>{}<br><br><br><b>{}</b><ul>{}</ul>".format(e.message, first_line, ''.join('<li>' + line for line in lines))

	index.exposed = True
	code.exposed = True

cherrypy.config.update({'server.socket_host': '0.0.0.0'})
cherrypy.config.update({'server.socket_port': int(os.environ.get('PORT', PORT))})
cherrypy.config.update({"environment": "embedded"})

OS = platform.system().upper()
print OS

if 'LINUX' in OS:
	os.system('clear')

elif 'WINDOWS' in OS:
	os.system('cls')


ip = [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
print
print "Configure your Amazon Developer Settings here first: https://developer.amazon.com/login.html, then then navigate to the 'Alexa' developer setting console."
print "Make sure you whitelist: http://localhost:{} and http://localhost:{}/code in 'Allowed Origins' and 'Allowed Return URLs' respectfully.".format(PORT, PORT)
print

print
print
print
print("Now navigate to http://{}:{} or http://localhost:{} to begin the auth process".format(ip, PORT, PORT))
print "(Press Ctrl-C to exit this script once authorization is complete)"
print
print
print

cherrypy.quickstart(Start())
