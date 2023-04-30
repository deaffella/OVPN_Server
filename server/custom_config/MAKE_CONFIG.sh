#!/bin/bash

# Скрипт для создания `openvpn.conf` и `ovpn_env.sh`.
#
# USAGE:
# sudo ./MAKE_CONFIG.sh --ext_ip 217.144.98.104 --subnet 192.168.42.0 --mask 24

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root"
  exit
fi

export config_file="openvpn.conf"
export env_file="ovpn_env.sh"


# Function to check if the provided flags exist
function check_flags() {
    local ext_ip_flag=false
    local subnet_flag=false
    local mask_flag=false

    for arg in "$@"; do
        case "$arg" in
            --ext_ip)
                ext_ip_flag=true
                ;;
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

    if [[ $ext_ip_flag == true && $subnet_flag == true && $mask_flag == true ]]; then
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




# Save command line arguments
args=("$@")

# Check if all flags are present
if ! check_flags "${args[@]}"; then
    echo "Error: Missing one or more flags. Please provide --ext_ip, --subnet, and --mask."
    exit 1
fi

# Check and validate the IP address under --ext_ip flag
check_flag_value "--ext_ip" "${args[@]}"

# Check and validate the subnet address under --subnet flag
check_flag_value "--subnet" "${args[@]}"


# Get the ext_ip value
ext_ip_value=""
subnet_value=""
mask_value=""
for i in "${!args[@]}"; do
    if [[ "${args[$i]}" == "--ext_ip" ]]; then
        ext_ip_value="${args[$((i + 1))]}"
    fi
    if [[ "${args[$i]}" == "--subnet" ]]; then
        subnet_value="${args[$((i + 1))]}"
    fi
    if [[ "${args[$i]}" == "--mask" ]]; then
        mask_value="${args[$((i + 1))]}"
    fi
done


# Replace __SUBNET in config_file with the value from --subnet flag
replace_value "$config_file" "__SUBNET" "$subnet_value"

# Replace __SUBNET in $env_file with the value from --mask flag
replace_value "$env_file" "__SUBNET" "$subnet_value\/$mask_value"

# Replace __EXTERNAL_IP in $env_file with the value from --ext_ip flag
replace_value "$env_file" "__EXTERNAL_IP" "$ext_ip_value"

printf "

Done!
"