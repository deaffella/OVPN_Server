#!/bin/bash

# Скрипт для проброса одного порта с хоста на робота.
#
# USAGE:
#                               Внешний порт хоста      IP робота     Порт робота
# sudo ./forward_port_to_client.sh      SERVER_PORT       ROBOT_VPN_IP    ROBOT_PORT
# sudo ./forward_port_to_client.sh 32021 192.168.42.202 2021



if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root"
  exit
fi

#EXT_IP=`dig -4 TXT +short o-o.myaddr.l.google.com @ns1.google.com | sed 's/\"//g'`
EXT_IF=$(route 2>/dev/null | grep -m 1 '^default' | grep -o '[^ ]*$')   # eth0

SRC_PORT=$1             # Внешний порт хоста
DST_IP=$2               # IP робота в внутри vpn сети
DST_PORT=$3             # Конечный порт робота


iptables -t nat -A PREROUTING -p tcp --dport $SRC_PORT -j DNAT --to $DST_IP:$DST_PORT


printf "

SRC_PORT:  $SRC_PORT
DST_IP:    $DST_IP
DST_PORT:  $DST_PORT
EXT_IP:    $EXT_IP
INT_IF:    $INT_IF
EXT_IF:    $EXT_IF

"