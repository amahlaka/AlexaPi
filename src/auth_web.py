#! /usr/bin/env python

import os
import sys
import yaml
import json
import urllib
import socket
import logging
import platform
import requests
import cherrypy
import traceback

from cherrypy.process import servers
import alexa

if alexa.debug:
    cherrypy.log.error_log.propagate = True
    cherrypy.log.access_log.propagate = True

PORT = 5000
log = alexa.logger.getLogger(__name__)

class Start(object):
	def index(self):
		scope="alexa_all"
                try:
                    sd = json.dumps({
                            "alexa:all": {
                                    "productID": alexa.config['alexa']['ProductID'],
                                    "productInstanceAttributes": {
                                            "deviceSerialNumber": "001"
                                    }
                            }
                    })

                    url = "https://www.amazon.com/ap/oa"
                    callback = cherrypy.url()  + "code"

                except (BaseException, Exception) as e:
                    return self.catch_error(e)

                payload = {"client_id" : alexa.config['alexa']['Client_ID'], "scope" : "alexa:all", "scope_data" : sd, "response_type" : "code", "redirect_uri" : callback }
                req = requests.Request('GET', url, params=payload)
                p = req.prepare()
                raise cherrypy.HTTPRedirect(p.url)

	def code(self, var=None, **params):
                try:
                    code = urllib.quote(cherrypy.request.params['code'])
                    callback = cherrypy.url()
                    payload = {"client_id" : alexa.config['alexa']['Client_ID'], "client_secret" : alexa.config['alexa']['Client_Secret'], "code" : code, "grant_type" : "authorization_code", "redirect_uri" : callback }
                    url = "https://api.amazon.com/auth/o2/token"
                    r = requests.post(url, data = payload)
                    resp = r.json()

                    alexa.set_variable(['alexa', 'refresh_token'], resp['refresh_token'])

                    return "<h2>Success!</h2><h3> Refresh token has been added to your config file, you may now reboot the Pi </h3><br>{}".format(resp['refresh_token'])

                except Exception as e:
                    return self.catch_error(e)

        def catch_error(self, e):
            log.exception('\n\n' + e.message + '\n\n')
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            first_line = lines[0]
            lines.pop(0)
            return "<h2>INTERNAL ERROR!</h2><h3> An internal error occured! Error message: </h3><br>{}<br><br><br><b>{}</b><ul>{}</ul>".format(e.message, first_line, ''.join('<li>' + line for line in lines))

	index.exposed = True
	code.exposed = True

cherrypy.config.update({'server.socket_host': '0.0.0.0',})
cherrypy.config.update({'server.socket_port': int(os.environ.get('PORT', PORT)),})
cherrypy.config.update({ "environment": "embedded" })

ip =[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

OS = platform.system().upper()
print OS

if 'LINUX' in OS:
    os.system('clear')

elif 'WINDOWS' in OS:
    os.system('cls')

print
print "Configure your Amazon Developer Settings here first: https://developer.amazon.com/login.html, then then navigate to the 'Alexa' developer setting console."
print "Make sure you whitelist: http://localhost:{} and http://localhost:{}/code in 'Allowed Origins' and 'Allowed Return URLs' respectfully.".format(PORT, PORT)
print
print "(Your IP address: {})".format(ip)

print
print
print
print "Now navigate to http://localhost:5000 to begin the auth process"
print "(Press Ctrl-C to exit this script once authorization is complete)"
print
print
print

cherrypy.quickstart(Start())
