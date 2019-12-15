#!/usr/bin/env bash
cat old_file.txt|while read line
do
  old_name=`echo $line|awk -F '/' '{print $NF}'`
  path=`echo ${line}|awk -F '/' '{for(i=1;i<NF;i++){printf $i"/"} ;printf "\n"}'`
  if grep "$old_name" file.txt >/dev/null
  then
    old_path=`grep "$old_name" file.txt`
    new_name=`echo ${old_path}|sed  's#\./##g' |sed 's#/#_#g'`
    echo "mv $line $path$new_name"
    mv $line $path$new_name
  fi
done
