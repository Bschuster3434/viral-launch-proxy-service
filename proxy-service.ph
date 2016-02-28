#!/usr/bin/python

import threading
import atexit

import yaml, sys
import json

import urllib, time

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
			url = 'http://www.timeapi.org/utc/now.json?q=%d' % time.time()
			try: 
				response = urllib.urlopen(url)
			except:
				pass
			print(proxy)
			print(proxy_list)
			if response.getcode() != 200: 
				print("Response: %d" % response.getcode())
				proxy['working'] = False
			else:
				print("Response: %s" % response.read())
				proxy['working'] = True

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




@app.route('/')
def hello_world():
	return app.send_static_file('index.html')

@app.route('/proxy_list')
def list_proxies():
	if request.args.get('json', True) is False:
		return yaml.dump( proxy_list )
	else:
		return json.dumps( proxy_list )



if __name__ == '__main__':
	atexit.register(shutdown_thread)
	print("Starting app.")
	app.before_first_request(start_thread)
	app.run( host='0.0.0.0', debug=True )
