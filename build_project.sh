#!/bin/bash

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root"
  exit
fi
clear

export internal_vpn_subnet="192.168.42.0/24"

export docker_stack_name="openvpn"
export project_dir_path=`pwd`/
export OS_PLATFORM=`uname -s`/`uname -m`

printf "\n\n[---] Trying to build stack:
    docker_stack_name:\t\t${docker_stack_name}
    project_dir:\t\t${project_dir_path}
    os platform:\t\t${OS_PLATFORM}\n\n"
sleep 1

cd ${project_dir_path}
COMPOSE_DOCKER_CLI_BUILD=1 \
DOCKER_BUILDKIT=1 \
docker-compose -p "${docker_stack_name}" up -d --build
printf "\n\n[---] BUILD SUCCESSFUL\n"

printf "\n[!!!] WARNING! READ THIS MESSAGE PLEASE!\n
    Now we will try to move config files into the docker volume.\n\n"
cp custom_config/openvpn.conf custom_config/config/openvpn.conf
printf "\n[---] Copy done.\n
    Start rebooting ovpn_container to apply new config.\n\n"
docker restart ovpn_server

docker_container_addr=`docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ovpn_server`
printf "\n[!!!] WARNING! READ THIS MESSAGE PLEASE!\n
    Now we will try to remove old route and create new one.
    If you are not sure about the correctness of the subnet below,
    edit it inside this script and run it outside!\n
    Current subnet is: $internal_vpn_subnet
    Docker container internal ip: $docker_container_addr\n\n"
sleep 2

printf "\n[---] Trying to delete old route:\n"
ip route del $internal_vpn_subnet

printf "\n[---] Trying to create new route\n"
ip ro add $internal_vpn_subnet via $docker_container_addr



