#!/bin/bash

# The id file contains my own link to the ontv content
ID=`cat /home/kenneth/scripts/update_program/id`

cd /media/multimedia/logs/update_program

now=`date +%s`
last=`cat last`
diffe=$(( $now-$last ))

# Only pull the program if it is more than one day since we did it last
if [ $diffe -gt 86400 ];then
    wget -nd -m http://ontv.dk/xmltv/$ID
    if [ $? -eq 0 ];then
	echo $now > last
	logstring="$(date) === Diff: $diffe, Pull OK"
    else
	logstring="$(date) === Diff: $diffe, Pull FAILED"
    fi

    mythfilldatabase --file --sourceid 1 --xmlfile $ID
    if [ $? -eq 0 ];then
	logstring="$logstring, Update OK"
    else
	logstring="$logstring, Update FAILED"
    fi

    echo $logstring >> log
fi
