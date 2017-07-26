#!/usr/bin/python

import threading
import atexit

import traceback

import yaml, sys
import json

import urllib2, urllib, time

import docker

import unicodedata

from flask import Flask
from flask import request, Response

# sys.exit when we reach this time.  This will clear out the proxies and start again.
max_run_time = time.time()+3600
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
	if time.time() > max_run_time:
		print "NOT Restarting to clear proxies"
		#sys.exit()
	with data_lock:
		#print(proxy_list)
		#proxy_list['proxy_list'].append( { 'id' : 'four' } )

		# Step through the list of proxies and test them.
		for proxy in proxy_list['proxy_list']:
			if not proxy['enabled']:
#				if 'docker' in proxy:
#					print "Proxy is a docker proxy.. restarting it."
#					docker_cli.restart(proxy['docker']['tor'])
#					docker_cli.restart(proxy['docker']['polipo'])
				print "Proxy %s is disabled.. skipping." % proxy['id']
				print("SKIPPED")
				proxy['working'] = False
				proxy['response'] = 'NA'
				continue
			print "Going to hit %s" % proxy['id']
			url = '%s?q=%d' % ( proxy_list['testing_url'], time.time() )
			result=500
			request_time = 10000
			data = 'NONE'
			try: 
				start_time = time.time()
				proxy_handler = urllib2.ProxyHandler({'http':proxy['url']})
				opener = urllib2.build_opener(proxy_handler)
				urllib2.install_opener(opener)
				response = urllib2.urlopen(url, timeout= 10)

				# Old working method
				#response = urllib.urlopen(url, proxies={'http':proxy['url']} )
				result=response.getcode()
				data = response.read()
				request_time = time.time() - start_time
			except Exception as e:
				print "Error: "
				print traceback.format_exc()
				pass
			print(proxy)
			#print(proxy_list)
			if result != 200 or request_time > proxy_list['max_request_time'] or "lightspeed" in data: 
				print("FAILED Response: %d in %d time CONTENT: %d" % ( result, request_time, "lightspeed" in data ))
				proxy['working'] = False
				proxy['response'] = 'NA'
				if 'docker' in proxy:
					docker_cli.restart(proxy['docker']['tor'])
					docker_cli.restart(proxy['docker']['polipo'])
			else:
				print("Response: %s" % result)
				proxy['working'] = True
				proxy['response'] = data
				proxy['result'] = result
				proxy['time'] = request_time

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
        	if ( entry['working'] is True or entry['working'] == 1 ) and (entry['enabled'] is True or entry['enabled'] == 1 ):
                	new_list.append(entry)
	new_dict = dict()
	new_dict['proxy_list'] = new_list

	return new_dict


@app.route('/')
def hello_world():
	return app.send_static_file('index.html')

@app.route('/add_proxy/<id>/<url>')
def add_proxy( id, url ):
	id = int(unicodedata.normalize('NFKD', id).encode('ascii','ignore'))
	clean_url = unicodedata.normalize('NFKD', url).encode('ascii','ignore')
	check_url = clean_url.replace('_', '/')

	for entry in proxy_list['proxy_list']:
		#print "Checking to add %s = %s" % (check_url, entry['url'])
		if entry['url'] == check_url:
			print "Skipping.. already exists."
			return "Proxy ignored: %s %s" % ( id, url.replace('_', '/') )

	print "Not found.. adding"
	proxy_list['proxy_list'].append( { 'id' : id, 'url' : clean_url.replace('_', '/'), 'enabled':True, 'working':True  } )
	return "Proxy added: %s %s" % ( id, url.replace('_', '/') )


@app.route('/enable_proxy/<url>')
def enable_proxy( url ):
	clean_url = unicodedata.normalize('NFKD', url).encode('ascii','ignore')
	check_url = clean_url.replace('_', '/')

	# Step through the proxies looking for either id or URL
	for proxy in proxy_list['proxy_list']:
		if isinstance( proxy['id'], (int, long))  or proxy['url'] == clean_url:
			#proxy_list['proxy_list'].append( { 'id' : id, 'url' : clean_url.replace('_', '/'), 'enabled':True, 'working':False } )

			for entry in proxy_list['proxy_list']:
				print "Checking to disable %s = %s" % (check_url, entry['url'])
				if entry['url'] == check_url:
					print "Enabling %s" % clean_url
					entry['enabled'] = True
					entry['working'] = True

			return "Proxy enabled: %s" % ( clean_url )

	return "Could not find: %s" % ( clean_url )

@app.route('/disable_proxy/<url>')
def disable_proxy( url ):
	clean_url = unicodedata.normalize('NFKD', url).encode('ascii','ignore')
	check_url = clean_url.replace('_', '/')

	# Step through the proxies looking for either id or URL
	for proxy in proxy_list['proxy_list']:
		if isinstance( proxy['id'], (int, long))  or proxy['url'] == clean_url:
			#proxy_list['proxy_list'].append( { 'id' : id, 'url' : clean_url.replace('_', '/'), 'enabled':False, 'working':False } )

			for entry in proxy_list['proxy_list']:
				print "Checking to disable %s = %s" % (check_url, entry['url'])
				if entry['url'] == check_url:
					print "Disabling %s" % clean_url
					entry['enabled'] = False
					#entry['working'] = False


			return "Proxy disabled: %s" % ( clean_url )
	return "Could not find: %s" % ( clean_url )

@app.route('/write_config/<filename>')
def write_config(filename):
	with open(filename, 'w') as outfile:
		outfile.write( yaml.dump( proxy_list, default_flow_style=False) )
	return "File written"

@app.route('/proxy_list')
def list_proxies():
	if request.args.get('json', True) is False:
		return yaml.dump( proxy_list )
	else:
		return json.dumps( proxy_list )

@app.route('/proxy_list_filtered')
def list_proxies_filtered():

	blocked_id = request.args.get('blocked', 'None')
	if blocked_id != 'None':
		print "Got a blocked URL back from the scraper: %s" % blocked_id
		for entry in proxy_list['proxy_list']:
			#print "Checking: %s and %s" % ( entry['id'], blocked_id )
			if str(entry['id']) == str(blocked_id):
				print "Told to disable %s" % blocked_id
				entry['enabled'] = False
				entry['working'] = False

	if request.args.get('json', True) is False:
		return yaml.dumps( strip_proxy_list(proxy_list) )
	else:
		return json.dumps( strip_proxy_list(proxy_list) )



if __name__ == '__main__':
	atexit.register(shutdown_thread)
	print("Starting app.")
	app.before_first_request(start_thread)
	app.run( host='0.0.0.0', port=5001, debug=True )
