#!/usr/bin/env bash

#需要先把文件切割成900行的小文件，否则会出现内存溢出情况
findfile()
{
	if [ ! -n $1   ]
	then
	  continue
	fi
	sleep 3
	if grep "$1" file.txt-bak >>nas.txt
	then
		size=`grep "$1" file.txt-bak|awk '{print $1}'`
		exec echo "$size    $2" >>newfile.txt
	fi
}


for i in `ls|grep -v txt`
do
	cat $i|while read line
		do
		{
		  name=`echo ${line}|awk -F '_' '{print $(NF-2)"_"$(NF-1)"_"$NF}'`
		  findfile $name $line
		} &
		done
	sleep 1
done

