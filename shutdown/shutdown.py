#!/usr/bin/env python

import xml.etree.ElementTree
import subprocess
import time
import datetime
import urllib
import sys
import json
import urllib2

### Settings 
#.................... EDIT HERE START
XML_FILE_NAME = 'http://127.0.0.1:6544/Status/GetStatus'
# Estimated fall a sleep and wake up time
SLEEP_WAKEUP_TIME = 600
#.................... EDIT HERE END

def send_notification():
    """Ask xbmc to quit if open"""
    title = "Recording running or pending"
    message = "Please leave the mediacenter running. It will shut itself down, when it "\
        "is done"
    params = {"title": title, "message": message, "displaytime": 11000}
    to_send = {"jsonrpc": "2.0", "method": "GUI.ShowNotification", "params": params}
    to_send = json.dumps(to_send)
    to_send = urllib2.quote(to_send, '')
    url = 'http://localhost:8080/jsonrpc?request={}'.format(to_send)
    try:
        response = urllib2.urlopen(url)
        html = response.read()
        response.close()
        out = True
    except urllib2.URLError:
        out = False
    return out

def xbmc_quit():
    """Ask xbmc to quit if open"""
    to_send = {"jsonrpc": "2.0", "method": "Application.Quit"}
    to_send = json.dumps(to_send)
    to_send = urllib2.quote(to_send, '')
    url = 'http://localhost:8080/jsonrpc?request={}'.format(to_send)
    try:
        response = urllib2.urlopen(url)
        html = response.read()
        response.close()
        out = True
    except urllib2.URLError:
        out = False
    return out

def main():
    ### Initial assignments ###
    now = int(time.mktime(datetime.datetime.now().timetuple()))
    
    # Read the status xml file to a eTree object
    xmlfile = urllib.urlopen(XML_FILE_NAME)
    xmlcontent = xml.etree.ElementTree.parse(xmlfile)
    xmlfile.close()
    
    # List of statusses for tv-cards, 0 is inactive
    encoder_statusses = [int(enc.attrib['state']) for enc in
                         xmlcontent.find('Encoders').getchildren()]
    if sum(encoder_statusses) > 0:
        send_notification()
        sys.exit(1)
    
    # Find next recording
    rec = []
    UTC_OFFSET = datetime.datetime.utcnow() - datetime.datetime.now()
    for program in xmlcontent.find('Scheduled').getchildren():
        # The format is '2014-02-22T14:25:00Z' and it is UTC or ZULU time
        from_db = program.find('Recording').attrib['recStartTs']
        utc_time = datetime.datetime.strptime(from_db[:-1], '%Y-%m-%dT%H:%M:%S')
        # Calculate local time
        localtime = utc_time - UTC_OFFSET
        # Convert to time object to get epoch time
        epochtime = time.mktime(localtime.timetuple())
        print epochtime
        rec.append(int(epochtime))
    
    best_item = min(rec) if len(rec) > 0 else None
    
    # If there is no recording in the future
    if best_item is not None:
        difference = best_item - now
        if difference > 0 and difference < 1200:
            send_notification()
            sys.exit(1)

    xbmc_quit()
    time.sleep(2)
    subprocess.Popen('sudo shutdown -P now', shell=True)
    time.sleep(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
