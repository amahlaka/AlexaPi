#! /usr/bin/env python

import os
import yaml
import json
import urllib
import socket
import logging
import requests
import cherrypy

from cherrypy.process import servers
from alexa.config import config

cherrypy.log.error_log.propagate = False
cherrypy.log.access_log.propagate = False

class Start(object):
	def index(self):
		scope="alexa_all"
		sd = json.dumps({
			"alexa:all": {
				"productID": config['alexa']['ProductID'],
				"productInstanceAttributes": {
					"deviceSerialNumber": "001"
				}
			}
		})
		url = "https://www.amazon.com/ap/oa"
		callback = cherrypy.url()  + "code"
		payload = {"client_id" : config['alexa']['Client_ID'], "scope" : "alexa:all", "scope_data" : sd, "response_type" : "code", "redirect_uri" : callback }
		req = requests.Request('GET', url, params=payload)
		p = req.prepare()
		raise cherrypy.HTTPRedirect(p.url)

	def code(self, var=None, **params):
		code = urllib.quote(cherrypy.request.params['code'])
		callback = cherrypy.url()
		payload = {"client_id" : config['alexa']['Client_ID'], "client_secret" : config['alexa']['Client_Secret'], "code" : code, "grant_type" : "authorization_code", "redirect_uri" : callback }
		url = "https://api.amazon.com/auth/o2/token"
		r = requests.post(url, data = payload)
		resp = r.json()

		alexapi.config.set_variable(['alexa', 'refresh_token'], resp['refresh_token'])

		return "<h2>Success!</h2><h3> Refresh token has been added to your config file, you may now reboot the Pi </h3><br>{}".format(resp['refresh_token'])
	index.exposed = True
	code.exposed = True

cherrypy.config.update({'server.socket_host': '0.0.0.0',})
cherrypy.config.update({'server.socket_port': int(os.environ.get('PORT', '5000')),})
cherrypy.config.update({ "environment": "embedded" })


ip =[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

print "Configure your Amazon Developer Settings here first: https://developer.amazon.com/login.html, then then navigate to the 'Alexa' developer setting console."
print "Ready goto http://{}:5000 or http://localhost:5000  to begin the auth process".format(ip)
print "(Press Ctrl-C to exit this script once authorization is complete)".format(ip)

cherrypy.quickstart(Start())
