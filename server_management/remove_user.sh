#!/bin/bash

# Скрипт для добавления нового пользователя впн.
#
# USAGE:
# sudo bash remove_user.sh --name MB1



if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root"
  exit
fi


while [ -n "$1" ]
do
case "$1" in
--name) name="$2"
shift ;;
--) shift
break ;;
*) echo "$1 is not an option";;
esac
shift
done


docker-compose run --rm ovpn_server ovpn_revokeclient $name remove

rm ../custom_config/config/ccd/${name}
rm ./clients/${name}.ovpn