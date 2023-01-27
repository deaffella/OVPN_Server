#!/bin/bash

# Скрипт для восстановления iptables.
#
# USAGE:
# sudo ./iptables_restore.sh



if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root"
  exit
fi


check_iptables_backup() {
  # Проверяет наличие файла с бэкапом iptables.
  # Если бэкап существует, прогружает данные из него и применяет новые провила.
  # Если бэкапа нет, создает его и применяет новые провила.

  #iptables_backup_dir=/VPN_iptables
  iptables_backup_dir=./iptables
  iptables_backup_file=$iptables_backup_dir/backup.txt

  printf "==================================================
[ 00 ] Trying to read and apply iptables rules from backup file:
       - [${iptables_backup_file}]
"

  if [ -e "${iptables_backup_file}" ]; then
    printf "==================================================
[ 01 ] Iptables backup file exists:
       - [${iptables_backup_file}]
"

  else
    printf "==================================================
[ 01 ] Iptables backup DOES NOT exisT!
       Trying to create backup file:
       - [${iptables_backup_file}]
"
    iptables-save > ${iptables_backup_file}          # [">" to save rules]
    printf "==================================================
[ 01 ] Iptables backup created:
       - [${iptables_backup_file}]
"
  fi


  iptables-restore < ${iptables_backup_file}       # ["<" to load rules]
  printf "==================================================
[ 02 ] Iptables restore complete:
       - [${iptables_backup_file}]
"
}




# загружаем бэкап iptables (если он есть)
check_iptables_backup

# применяем это правило, чтобы работали дальнейшие правила перенаправления портов на роботов
sudo iptables -A FORWARD -i eth0 -j ACCEPT