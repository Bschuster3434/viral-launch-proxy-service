#!/usr/bin/python

import threading
import atexit

import yaml, sys
import json

import urllib, time

import docker

from flask import Flask
from flask import request, Response

POLL_TIME = 60
data_lock = threading.Lock()
your_thread = threading.Thread()

app = Flask(__name__, static_url_path='/static')

proxy_list_file = 'list_of_proxies.yml'

try:
	with open( proxy_list_file, 'r') as f:
		proxy_list = yaml.load(f)
except:
	print("Can not load proxy list")
	sys.exit()

docker_cli = docker.Client(base_url = 'unix://var/run/docker.sock', version='auto')

# This is called by atexit
def shutdown_thread():
	print("Shutting down and cleaning up.")
	your_thread.cancel()

# This will be called every POLL_TIME seconds
def process_thread():
	print("Processing thread with count! %d" % threading.active_count())
	with data_lock:
		#print(proxy_list)
		#proxy_list['proxy_list'].append( { 'id' : 'four' } )

		# Step through the list of proxies and test them.
		for proxy in proxy_list['proxy_list']:
			print "Going to hit %s" % proxy['id']
			url = '%s?q=%d' % ( proxy_list['testing_url'], time.time() )
			result=500
			try: 
				response = urllib.urlopen(url, proxies={'http':proxy['url']})
				result=response.getcode()
			except:
				pass
			print(proxy)
			print(proxy_list)
			if result != 200: 
				print("FAILED Response: %d" % result)
				proxy['working'] = False
				proxy['response'] = 'NA'
				docker_cli.restart(proxy['docker']['tor'])
				docker_cli.restart(proxy['docker']['polipo'])
			else:
				print("Response: %s" % result)
				proxy['working'] = True
				proxy['response'] = response.read()

	your_thread = threading.Timer(POLL_TIME, process_thread, ())
	your_thread.start()
	print("Started thread: %s" % your_thread.ident)

# Now go fire the thread for the first time.
def start_thread():
	print("Starting thread! %d" % threading.active_count())
	# POLL_TIME = 1 here to fire immedately
	your_thread = threading.Timer(1, process_thread, ())
	your_thread.start()
	print("Initial Start thread %s!" % your_thread.ident)

def strip_proxy_list( proxy_list ):
	new_list = list()
	for entry in proxy_list['proxy_list']:
        	if entry['working'] is True:
                	new_list.append(entry)
	new_dict = dict()
	new_dict['proxy_list'] = new_list

	return new_dict


@app.route('/')
def hello_world():
	return app.send_static_file('index.html')

@app.route('/proxy_list')
def list_proxies():
	if request.args.get('json', True) is False:
		return yaml.dump( proxy_list )
	else:
		return json.dumps( proxy_list )

@app.route('/proxy_list_filtered')
def list_proxies_filtered():
	if request.args.get('json', True) is False:
		return yaml.dumps( strip_proxy_list(proxy_list) )
	else:
		return json.dumps( strip_proxy_list(proxy_list) )



if __name__ == '__main__':
	atexit.register(shutdown_thread)
	print("Starting app.")
	app.before_first_request(start_thread)
	app.run( host='0.0.0.0', debug=True )
