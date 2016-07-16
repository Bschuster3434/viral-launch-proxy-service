#!/usr/bin/python

import socket
socket.setdefaulttimeout(1)

import urllib, json, time, sys

testing_url="http://iq-colo.sneaky.net/cgi-bin/ip.py"
timeout = 1
url = 'http://gimmeproxy.com/api/getProxy?country=US&supportsHttps=true&protocol=http'
#url = 'http://127.0.0.1:5000/proxy_list_filtered '

Debug = False;


def find_proxy( url, timeout, testing_url):

	try:
		response = urllib.urlopen( url )
	except:
		if Debug: print "Request to get proxy failed."
		return (False, False)

	result=response.getcode()

	content = response.read()

	data = json.loads( content )

	if Debug: print data['curl']

	start_time = time.time()

	try:
		response = urllib.urlopen(testing_url, proxies={'http':data['curl']})
	except:
		if Debug: print "Proxy test request failed."
		return (False, False)

	result=response.getcode()
	request_time = time.time() - start_time

	if result == 200: 
		if Debug: print "\n\nGot test url with %d in %f seconds" % (result, request_time)
		return (data['curl'], request_time)


	else:
		if Debug: print "Failed with %d" % result
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
		print "curl -s http://127.0.0.1:5000/add_proxy/%s/%s" % (id, urllib.quote(proxy_url.replace('/','_')))
		response = urllib.urlopen( "http://127.0.0.1:5000/add_proxy/%d/%s" % (id, urllib.quote(proxy_url.replace('/','_')) ))
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


