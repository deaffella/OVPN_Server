#!/bin/bash

# Скрипт для создания `openvpn.conf` и `ovpn_env.sh`.
#
# USAGE:
# sudo bash MAKE_CONFIG.sh --subnet 192.168.42.0 --mask 24


if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root"
  exit
fi
clear

export dst_config_dir="./config/"
export dst_config_file="$dst_config_dir/openvpn.conf"
export dst_env_file="$dst_config_dir/ovpn_env.sh"
export dev_container_name=ovpn_server_dev

ext_ip_value=`curl -s http://whatismijnip.nl |cut -d " " -f 5`

rm -r ./config/ccd ./config/pki ./config/openvpn* ./config/ovpn* ./config/*.pem

# Function to check if the provided flags exist
function check_flags() {
    local subnet_flag=false
    local mask_flag=false

    for arg in "$@"; do
        case "$arg" in
            --subnet)
                subnet_flag=true
                ;;
            --mask)
                mask_flag=true
                ;;
            *)
                ;;
        esac
    done

    if [[ $subnet_flag == true && $mask_flag == true ]]; then
        return 0
    else
        return 1
    fi
}

# Function to validate IP address and subnet format
function valid_ip_or_subnet() {
    local ip_or_subnet=$1
    local stat=1

    if [[ $ip_or_subnet =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        ip_or_subnet=($ip_or_subnet)
        IFS=$OIFS
        [[ ${ip_or_subnet[0]} -le 255 && ${ip_or_subnet[1]} -le 255 && ${ip_or_subnet[2]} -le 255 && ${ip_or_subnet[3]} -le 255 ]]
        stat=$?
    fi

    return $stat
}

# Function to check and validate the IP address or subnet under the given flag
function check_flag_value() {
    local flag_name=$1
    local args=("${@:2}")
    local flag_value=""

    for i in "${!args[@]}"; do
        if [[ "${args[$i]}" == "$flag_name" ]]; then
            flag_value="${args[$((i + 1))]}"
            break
        fi
    done

    if [[ -z $flag_value ]]; then
        echo "Error: $flag_name flag is missing or has no value."
        exit 1
    elif ! valid_ip_or_subnet $flag_value; then
        echo "Error: Invalid IP address or subnet format for $flag_name."
        exit 1
    fi
}


# Function to replace some value in the specified file with the provided value
function replace_value() {
    local config_file=$1
    local to_replace_value=$2
    local replace_text_value=$3

    if [[ -z $subnet_value ]]; then
        echo "Error: new value is missing."
        exit 1
    fi

    if [[ ! -f $config_file ]]; then
        echo "Error: $config_file not found in the current directory."
        exit 1
    fi

    # Replace src value with the new value in the specified file
    sed -i "s/$to_replace_value/$replace_text_value/g" $config_file
}

# Function to make volume with ovpn configuration
function make_ovpn_conf_volume() {
    printf "\n\nNow we will try to pull ovpn docker image and make some magic to configure it!\n\n"
    local OVPN_VOLUME_NAME="ovpn-data-container"

    printf "[---] Trying to remove existing conf volume with name: $OVPN_VOLUME_NAME\n"
    docker volume rm $OVPN_VOLUME_NAME
    printf "[---] Trying to create new conf volume with name: $OVPN_VOLUME_NAME\n"
    docker volume create --name $OVPN_VOLUME_NAME --opt type=none --opt device=`pwd`/config --opt o=bind
    sleep 1
    printf "\n[---] Trying to run ovpn_genconfig\n"
    docker run -v $OVPN_VOLUME_NAME:/etc/openvpn --rm  --name $dev_container_name kylemanna/openvpn ovpn_genconfig -u udp://$ext_ip_value
    printf "\n[---] Trying to run ovpn_initpki\n\n"
    printf "\n[!!!] WARNING! READ THIS MESSAGE PLEASE!\n
    In the following dialogs, you will need to
    enter the AUTHORIZATION PASS PHRASE several times.
    Come up with a key that you won't be able to forget.
    It will be used when creating client certificates!\n
    AUTHORIZATION PASS PHRASE REQUIREMENTS:
    - length from 4 to 1023;
    - digits and latin letters;
    \n\n\n"
    sleep 2
    docker run -v $OVPN_VOLUME_NAME:/etc/openvpn --rm -it --name $dev_container_name kylemanna/openvpn ovpn_initpki

}


# Save command line arguments
args=("$@")

# Check if all flags are present
if ! check_flags "${args[@]}"; then
    echo "Error: Missing one or more flags. Please provide --subnet, and --mask."
    exit 1
fi


# Check and validate the subnet address under --subnet flag
check_flag_value "--subnet" "${args[@]}"

subnet_value=""
mask_value=""
for i in "${!args[@]}"; do
    if [[ "${args[$i]}" == "--subnet" ]]; then
        subnet_value="${args[$((i + 1))]}"
    fi
    if [[ "${args[$i]}" == "--mask" ]]; then
        mask_value="${args[$((i + 1))]}"
    fi
done

make_ovpn_conf_volume

printf "\n[!!!] WARNING! READ THIS MESSAGE PLEASE!\n
    Now we will try to move config files into the docker volume.\n\n"
printf "[---] Copy mock files to \`./config/\`:\n"
cp mock/openvpn.conf $dst_config_file
cp mock/ovpn_env.sh $dst_env_file

printf "\n[---] Trying to make changes in conf files:\n - $dst_config_file\n - $dst_env_file\n"
replace_value "$dst_config_file" "__SUBNET" "$subnet_value"               # Replace __SUBNET in $dst_config_file with the value from --subnet flag
replace_value "$dst_config_file" "__EXTERNAL_IP" "$ext_ip_value"          # Replace __EXTERNAL_IP in $dst_config_file with the value from --subnet flag
replace_value "$dst_env_file"    "__SUBNET" "$subnet_value\/$mask_value"  # Replace __SUBNET in $dst_env_file with the value from --mask flag
replace_value "$dst_env_file"    "__EXTERNAL_IP" "$ext_ip_value"          # Replace __EXTERNAL_IP in $dst_env_file with the value from --ext_ip flag
printf "\n[---] Conf files was changed!\n"


