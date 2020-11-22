#!/bin/bash 
echo "Setting default sink to: $1";
pacmd set-default-sink $1
pacmd list-sink-inputs | grep index | while read line
do
	echo "Moving input: $line";
	echo $line | cut -d' ' -f2;
	echo "to sink: $1";
	pacmd move-sink-input `echo $line | cut -d' ' -f2` $1

done
