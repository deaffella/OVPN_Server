#!/bin/bash

# Скрипт для добавления нового пользователя впн.
#
# USAGE:
# sudo ./create_user.sh --name MB1 --ip 192.168.42.201 --forward yes



if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root"
  exit
fi


while [ -n "$1" ]
do
case "$1" in
--name) name="$2"
shift ;;
--ip) ip="$2"
shift ;;
--forward) forward="$2"
shift;;
--) shift
break ;;
*) echo "$1 is not an option";;
esac
shift
done

# create cert
docker-compose run --rm megabot_vpn_server easyrsa build-client-full $name nopass

# create static client ip
echo "ifconfig-push $ip 255.255.255.0" > ./conf/ccd/$name

# copy cert to host
docker-compose run --rm megabot_vpn_server ovpn_getclient $name > ./clients/$name.ovpn

# forward ports
if [[ "$forward" == "yes" ]]; then
  LAST_OCTET=`echo "${ip}" | cut -d "." -f 4`
  ./forward_port_to_client.sh 3${LAST_OCTET}1 $ip 2021
  ./forward_port_to_client.sh 3${LAST_OCTET}2 $ip 2022
fi