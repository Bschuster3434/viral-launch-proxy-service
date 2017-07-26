#!/usr/bin/python

import socket
socket.setdefaulttimeout(1)

import urllib, json, time, sys

testing_url="http://iq-colo.sneaky.net/cgi-bin/ip.py"
timeout = 1
url = 'http://gimmeproxy.com/api/getProxy?country=US&supportsHttps=true&protocol=http'
#url = 'http://127.0.0.1:5001/proxy_list_filtered '

Debug = False;


if len(sys.argv) == 3:
	mode = sys.argv[1]
	proxy_url = sys.argv[2]
	print ( "http://127.0.0.1:5001/%s_proxy/%s" % (mode, urllib.quote(proxy_url.replace('/','_')) ))
	response = urllib.urlopen( "http://127.0.0.1:5001/%s_proxy/%s" % (mode, urllib.quote(proxy_url.replace('/','_')) ))
	print response.getcode()
	print response.read()
	

sys.exit()


