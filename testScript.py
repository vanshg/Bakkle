#!/usr/bin/python
# author: ajs
# license: bsd
# copyright: re2

import json 
import sys
import urllib2
import time

def successLights():
    req = urllib2.Request("http://sauron.rhventures.org:8765/lamp/A1/OFF")
    urllib2.urlopen(req)
    req = urllib2.Request("http://sauron.rhventures.org:8765/lamp/A2/OFF")
    urllib2.urlopen(req)
    req = urllib2.Request("http://sauron.rhventures.org:8765/lamp/A2/ON")
    urllib2.urlopen(req)

def failureLights():
    req = urllib2.Request("http://sauron.rhventures.org:8765/lamp/A2/OFF")
    urllib2.urlopen(req)
    req = urllib2.Request("http://sauron.rhventures.org:8765/lamp/A1/OFF")
    urllib2.urlopen(req)
    req = urllib2.Request("http://sauron.rhventures.org:8765/lamp/A1/ON")
    urllib2.urlopen(req)

###Health Check Solution
bldUrl = "http://rhv-bakkle-bld.rhventures.org:8000"
statusUrl = "/system/health/"

try:
    check = urllib2.urlopen(bldUrl + statusUrl)
except:
    print "URL Error: " + str(sys.exc_info()[0])
    failureLights()
    sys.exit(2)
try:
    buildStatus = json.load(check)
except:
    print "Failed to parse json"
    failureLights()
    sys.exit(3)

if buildStatus.has_key("health"):    
    if buildStatus["health"] == 1:
        successLights()
        print "Website is Healthy! Green GO! Red NO!"
    else:
        failureLights()
        print "Website has Croaked! Red GO! Green NO!"
else:
    sys.exit(5)

sys.exit(0)