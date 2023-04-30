# OVPN_Server
___

## Первоначальная настройка 
___

1. Клонировать проект.

   ```bash
   git@gitlab.smart-glow.ru:course_robots/OVPN_Server.git
   ```

2. Перейти в папку `custom_config` и изменить конфигурацию сервера
с помощью скрипта `MAKE_CONFIG.sh`:

   ```bash
   sudo bash MAKE_CONFIG.sh --ext_ip 217.144.98.104 --subnet 192.168.42.0 --mask 24
   ```
   
3. Вернуться в главную директорию `OVPN_Server`, указать правильную подсеть 
внутри скрипта `build_project.sh` (по дефолту используется `192.168.42.0/24`) 
и поднять проект:

   ```bash
   sudo bash build_project.sh
   ```


## Управление пользователями и сертификатами 
___

Для каждого созданного пользователя скопировать созданный сертификат из `./clients/` на 
клиента в директорию `/etc/openvpn/`, изменив расширение сертификата на `.conf`. 
Пример готового файла на роботе:
    
   ```bash
   /etc/openvpn/client.conf
   # service openvpn@client start   -   autoconnect on system startup
   ```
       
    
### Менеджмент пользователей 
___

Создать нового пользователя:
    
   ```bash
    sudo ./create_user.sh --name MB1 --ip 192.168.42.201
   ```

Удалить пользователя:
    
   ```bash
    sudo ./remove_user.sh --name MB1
   ```

Проверить существующие проброшенные порты:
    
   ```bash
    sudo iptables -L -n -t nat
   ```