#!/bin/bash
SCRIPT_PATH=$(cd "$(dirname "$0")";pwd)

function install_master(){
  sh ${SCRIPT_PATH}/bin/base_install.sh
  sh ${SCRIPT_PATH}/bin/master.sh
}

function install_node() {
  sh ${SCRIPT_PATH}/bin/base_install.sh
  sh ${SCRIPT_PATH}/bin/node.sh
}

usage()
{
cat << EOF
OPTION:
   1      install_master
   2      install_node
   0      exit
EOF
}
usage
read -p "Please input option:" option
case ${option} in
1)
  install_master
  ;;
2)
  install_node
  ;;
0)
  exit 0
  ;;
esac