#!/usr/bin/python

import socket
socket.setdefaulttimeout(1)

import urllib, json, time, sys, random

urllib.FancyURLopener.prompt_user_passwd = lambda *a, **k: (None, None) # Disable urlopen's password prompt (Dumb!)


testing_url="http://iq-colo.sneaky.net/cgi-bin/ip.py"
timeout = 10
url = 'http://gimmeproxy.com/api/getProxy?country=US&supportsHttps=true&protocol=http&api_key=ec7105f1-2609-4bfc-8907-4346a48fb821'
#url = 'http://gimmeproxy.com/api/getProxy?country=US&supportsHttps=true&protocol=socks4&api_key=ec7105f1-2609-4bfc-8907-4346a48fb821'
#url = 'http://127.0.0.1:5001/proxy_list_filtered '

Debug = False;


def find_proxy( url, timeout, testing_url):

	print "Requesting proxy address"
	socket.setdefaulttimeout(15)
	try:
		response = urllib.urlopen( url )
	except:
		"Request to get proxy failed."
		return (False, False)

	result=response.getcode()

	content = response.read()

	try:
		data = json.loads( content )
	except:
		print content
		sys.exit()

	if Debug: print data['curl']
	print "Testing returned proxy: %s" % data['curl']

	start_time = time.time()

	socket.setdefaulttimeout(10)
	try:
		response = urllib.urlopen(testing_url, proxies={'http':data['curl']})
	except:
		if Debug: print "Proxy test request failed."
		return (False, False)

	result=response.getcode()
	request_time = time.time() - start_time

	if result == 200 and "lightspeed" not in content: 
		if Debug: print "\n\nGot test url with %d in %f seconds" % (result, request_time)
		return (data['curl'], request_time)


	else:
		if Debug: print "Failed with %d and content %d" % (result, "lightspeed" in content)
		return (False, False)
tries = 0
proxy_url = False
while proxy_url is False:
	if Debug: print "Finding proxy.."
	tries += 1 
	( proxy_url, request_time ) = find_proxy(url, timeout, testing_url)
	#id = time.time()+random.randrange(1,1000)
	id = time.time()

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


