#!/usr/bin/env python

'''
This script is used to monitor the activity of a MythTV/xbmc box and put it to
sleep if inactive
'''

import time
import subprocess
import os
import sys
import re
import urllib
import urllib2
import json
import xml.etree.ElementTree
import MySQLdb

### Settings
#.................... EDIT HERE START
mysql_settings_file_name = '/etc/mythtv/mysql.txt'
xml_file_name = 'http://127.0.0.1:6544/Status/GetStatus'
log_file_name = '/media/multimedia/logs/check_for_inactivity/log'
other_activity_file_name = '/media/multimedia/logs/check_for_inactivity/other_activity'
# System sleep time in seconds
sys_sleep_time = 600
# List of program that will keep us awake
important_programs = ['totem', 'vlc', 'firefox', 'chromium', 'emacs', 'gedit',
                      'prboom', 'rsync', 'terminal', 'mythfrontend']
#.................... EDIT HERE END

# Parse mysql settings
with open(mysql_settings_file_name) as f:
    content = f.read()
host  = re.compile('^DBHostName=(.*)\n').search(content).groups()[0]
user  = re.compile('\nDBUserName=(.*)\n').search(content).groups()[0]
passw = re.compile('\nDBPassword=(.*)\n').search(content).groups()[0]
dbase = re.compile('\nDBName=(.*)\n').search(content).groups()[0]

### Functions ###
def xbmc_active():
    """Return a list of active players"""
    to_send = {"jsonrpc": "2.0", "method": "XBMC.GetInfoBooleans", "params": { "booleans": ["System.ScreenSaverActive "] }, "id": 1}
    to_send = json.dumps(to_send)
    to_send = urllib2.quote(to_send, '')
    url = 'http://localhost:8080/jsonrpc?request={}'.format(to_send)
    try:
        response = urllib2.urlopen(url)
        html = response.read()
        response.close()
        response = json.loads(html)
        out = not response['result']['System.ScreenSaverActive ']
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


def write_log(log_line):
    """Write the log line to the log"""
    if os.path.exists(log_file_name):
        with open(log_file_name, 'a') as f:
            f.write(log_line)
    else:
        with open(log_file_name, 'w') as f:
            f.write(log_line)
### End of functions, here starts the main code ###

# Initial variable initialisation
now = int(time.time())
log_line = time.strftime('%Y-%m-%d %T === ')
activity = False
if os.path.exists(other_activity_file_name):
    with open(other_activity_file_name) as f:
        other_activity = int(f.read())
else:
    other_activity = 0

# Close if xbmc is active
if xbmc_active():
    log_line += 'xbmc active'
    write_log(log_line + '\n')
    sys.exit(0)
else:
    log_line += 'xbmc not active'

# Read the content from the status xml file
xmlfile = urllib.urlopen(xml_file_name)
xmlcontent = xml.etree.ElementTree.parse(xmlfile)
xmlfile.close()

# List of statusses for tv-cards, 0 is inactive
encoder_statusses = [int(enc.attrib['state']) for enc in
                     xmlcontent.find('Encoders').getchildren()]
if sum(encoder_statusses) > 0:
    activity = activity or True
    log_line += ', act. rec'

# Mythweb session can be grabbed from the table mythweb_session
# Set up data base communication
db = MySQLdb.connect(host, user, passw, dbase)
cursor = db.cursor()
query = 'SELECT * FROM mythweb_sessions'
cursor.execute(query)
results = cursor.fetchall()

for item in results:
    if now - sys_sleep_time < time.mktime(item[1].timetuple()):
        activity = activity or True
        log_line += ', act. mythweb'

# Check whether a program is open that indicates that we want to keep it alive
process = subprocess.Popen('ps aux', shell=True, stdout=subprocess.PIPE).stdout
output = process.read()
process.close()

for program in important_programs:
    if output.find(program) > -1:
        activity = activity or True
        log_line += ', ' + program
        break  # One active program is enough

# Check if someone is logged in via ssh
process = subprocess.Popen('w', shell=True, stdout=subprocess.PIPE).stdout
output = process.read()
process.close()
##### Parse output like this
# 00:23:15 up  1:52,  3 users,  load average: 0.09, 0.09, 0.13
#USER     TTY      FROM              LOGIN@   IDLE   JCPU   PCPU WHAT
#kenneth  tty7                      22:30    1:52m 18.15s  0.01s /bin/sh /etc/xdg/xfce4/xinitrc -- /et
#kenneth  pts/3    knielsen-thinkpa 22:31    1:13m 13.25s  0.63s -bash
#kenneth  pts/4    knielsen-thinkpa 23:06    3.00s  0.59s  0.00s w
header = output.split('\n')[1]
start = header.find('FROM')
rest = output.split('\n')[2:]
for line in rest:
    if line[start:].split(' ')[0] != '':
        activity = activity or True
        log_line += ', ssh'
        break  # One active ssh session is enough

if activity:
    log_line += ', do nothing\n'
    write_log(log_line)
    with open(other_activity_file_name, 'w') as f:
        f.write(str(now))
    sys.exit(0)
elif (now - sys_sleep_time < other_activity):
    log_line += ', prev other act\n'
    write_log(log_line)
    sys.exit(0)
else:
    log_line += ', no act shutdown\n'
    write_log(log_line)
    xbmc_quit()
    time.sleep(5)
    subprocess.Popen('sudo halt -p', shell=True, executable="/bin/bash")
    sys.exit(0)
