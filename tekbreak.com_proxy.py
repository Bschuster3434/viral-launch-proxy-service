#!/usr/bin/python

import socket
socket.setdefaulttimeout(10)

import urllib, json, time, sys

testing_url="http://iq-colo.sneaky.net/cgi-bin/ip.py"
timeout = 10
#use_proxies = {'http':'http://204.13.205.143:8080'}
url = 'http://proxy.tekbreak.com/20/json'

Debug = False;

class AppURLopener(urllib.FancyURLopener):
	version = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.89 Safari/537.36'

#urllib._urlopener = AppURLopener()


def find_proxy( url, timeout, testing_url):

	

	socket.setdefaulttimeout(15)
	try:
		response = urllib.urlopen( url )
	except:
		if Debug: print "Request to get proxy failed."
		return (False, False)

	result=response.getcode()

	content = response.read()

	try:
		data = json.loads( content )
	except:
		print content
		sys.exit()

	print "got the data.. stepping through"
	# Step through the returned array
	url = 'None'
	for proxy in data:
		print proxy
		if proxy['country'] == 'USA' and proxy['type'] == 'HTTPS':
			print "Got USA"
			# {u'type': u'socks4/5', u'ip': u'121.42.189.206', u'time': u'1473535921', u'flag': u'http://proxy.tekbreak.com/cn.png', u'country': u'China', u'anonymity': u'High +KA', u'speed': {u'connection_time': {u'value': u'95'}, u'response_time': {u'value': u'94'}}, u'port': u'1080'}
			url = "%s://%s:%s" % (proxy['type'], proxy['ip'], proxy['port'])
			print "Here: %s" % url

	if url == 'None':
		sys.exit()


	if Debug: print url

	start_time = time.time()

	socket.setdefaulttimeout(1)
	try:
		response = urllib.urlopen(testing_url, proxies={'http':url})
	except:
		if Debug: print "Proxy test request failed."
		return (False, False)

	result=response.getcode()
	request_time = time.time() - start_time

	if result == 200 and "lightspeed" not in content: 
		if Debug: print "\n\nGot test url with %d in %f seconds" % (result, request_time)
		return (url, request_time)


	else:
		if Debug: print "Failed with %d and content %d" % (result, "lightspeed" in content)
		return (False, False)


tries = 0
proxy_url = False
while proxy_url is False:
	if Debug: print "Finding proxy.."
	tries += 1 
	( proxy_url, request_time ) = find_proxy(url, timeout, testing_url)
	id = int(time.time())

if proxy_url:

	if len(sys.argv) > 1:
		print "curl -s http://127.0.0.1:5001/add_proxy/%s/%s" % (id, urllib.quote(proxy_url.replace('/','_')))
		response = urllib.urlopen( "http://127.0.0.1:5001/add_proxy/%d/%s" % (id, urllib.quote(proxy_url.replace('/','_')) ))
		print response.getcode()
		print response.read()
		

	print "\n\n"
	print "  -"
	print "    tries: %d"%int(tries)
	print "    id: %d"%int(id)
	print "    request_time: %f"% request_time
	print "    enabled: 1"
	print "    url: \"%s\"" % proxy_url
	print "\n\n\n"

	sys.exit()


