#!/bin/bash

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root"
  exit
fi
clear



export docker_stack_name="openvpn"
export project_dir_path=`pwd`/
export OS_PLATFORM=`uname -s`/`uname -m`

printf "\n\n[---] Trying to build stack:
    docker_stack_name:\t\t${docker_stack_name}
    project_dir:\t\t${project_dir_path}
    os platform:\t\t${OS_PLATFORM}\n\n"
sleep 1


COMPOSE_DOCKER_CLI_BUILD=1 \
DOCKER_BUILDKIT=1 \
docker-compose -p "${docker_stack_name}" up -d --no-deps --build \
telegram_bot


