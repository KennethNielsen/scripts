#!/usr/bin/env python

'''This script is used to manually update the
/media/multimedia/logs/find_next_recording_time/next file with the
time of the next recording and to send that to the server over
udp. This script is meant to be executed by the system event handler
in Mythtv every time the scheduler has been run.
'''

import time
import datetime
import xml.etree.ElementTree
import sys
import urllib
import socket

### Settings 
#.................... EDIT HERE START
XML_FILE_NAME = 'http://127.0.0.1:6544/Status/GetStatus'
LOG_FILE_NAME = '/media/multimedia/logs/find_next_recording_time/log'
NEXT_FILE_NAME = '/media/multimedia/logs/find_next_recording_time/next'
SERVER_IP = '192.168.0.100'
SERVER_UDP_PORT = 9000
# Estimated fall a sleep and wake up time
SLEEP_WAKEUP_TIME = 600
#.................... EDIT HERE END

### Initial assignments ###
NOW = int(time.time())
LOG_LINE = time.strftime('%Y-%m-%d %T') + " === "

### Functions ###
def get_last_time():
    ''' Read the time that was identified for the next recording the last \
    time the script was run
    '''
    try:
        with open(NEXT_FILE_NAME) as file_:
            # NOTE We add the SLEEP_WAKEUP_TIME because it was subtracted when
            # the value was written
            last_time = int(file_.readline().strip('\n')) + SLEEP_WAKEUP_TIME
    except IOError:
        last_time = 0
    return last_time

def write_time(new_time):
    ''' Writes the time of the next recording to a local file and sends that \
    file to server.
    '''
    last_time = get_last_time()
    # Only do something if there has been a change
    if new_time != last_time:
        # Write wake up time to "next" file
        with open(NEXT_FILE_NAME, 'w') as file_:
            file_.write(str(new_time - SLEEP_WAKEUP_TIME))

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(str(new_time - SLEEP_WAKEUP_TIME),
                    (SERVER_IP, SERVER_UDP_PORT))

        return ' Time ' + str(new_time - SLEEP_WAKEUP_TIME) + ' written!'
    else:
        return ' Already updated!'

### End of functions, here start the main code ###
# Read the status xml file to a eTree object
def main():
    """The main method"""
    global LOG_LINE
    xmlfile = urllib.urlopen(XML_FILE_NAME)
    xmlcontent = xml.etree.ElementTree.parse(xmlfile)
    xmlfile.close()
    
    rec = []
    # Calculate the UTC offset
    UTC_OFFSET = datetime.datetime.utcnow() - datetime.datetime.now()
    for program in xmlcontent.find('Scheduled').getchildren():
        # The format is '2014-02-22T14:25:00Z' and it is UTC or ZULU time
        from_db = program.find('Recording').attrib['recStartTs']
        utc_time = datetime.datetime.strptime(from_db[:-1], '%Y-%m-%dT%H:%M:%S')
        # Calculate local time
        localtime = utc_time - UTC_OFFSET
        # Convert to time object to get epoch time
        epochtime = time.mktime(localtime.timetuple())
        rec.append(int(epochtime))
    
    best_item = min(rec) if len(rec) > 0 else None
    
    # If there is no recording in the future
    if best_item is None:
        LOG_LINE += ' No rec. in fut.'
        # The return value from write_time is a part of the log line
        LOG_LINE += write_time(0) + '\n'
        with open(LOG_FILE_NAME, 'a') as file_:  # 'a' is append
            file_.write(LOG_LINE)
        sys.exit(0)
    
    # If next is more than SLEEP_WAKEUP_TIME into the future, then write the
    # time to the 'next' file
    if best_item - NOW > SLEEP_WAKEUP_TIME:
        LOG_LINE += ' Rec. scheduled.'
        # The return value from write_time is a part of the log line
        LOG_LINE += write_time(best_item) + '\n'
        with open(LOG_FILE_NAME, 'a') as file_: # 'a' is append
            file_.write(LOG_LINE)
        sys.exit(0)


if __name__ == '__main__':
    main()
