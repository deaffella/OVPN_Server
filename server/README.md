### Первоначальная настройка 
___

1. Клонировать проект.

2. Перейти в папку `server/custom_config` и изменить настройки внутри 
`openvpn.conf` и `ovpn_env.sh` с помощью скрипта `MAKE_CONFIG.sh`:

   ```
   # Пример:
   sudo ./MAKE_CONFIG.sh --ext_ip 217.144.98.104 --subnet 192.168.42.0 --mask 24
   ```

3. Инициализировать конфигурационные файлы и сертификаты.
    
    ```
    docker run --rm kylemanna/openvpn ovpn_genconfig -u udp://${HOST_EXTERNAL_ADDR}
    docker run --rm kylemanna/openvpn ovpn_initpki
    
    EXAMPLE: 
    docker run --rm kylemanna/openvpn ovpn_genconfig -u udp://217.144.98.104
    docker run --rm kylemanna/openvpn ovpn_initpki
    ```

4. Поднять проект с помощью `./build_project.sh`.

5. После поднятия контейнера с сервером:

    * Положить файлы из директории `server/custom_config/` в `server/conf/`.
    
    ```
    ip ro add ${VPN_INTERNAL_ADDR} via ${VPN_CONTAINER_INTERNAL_ADDR}
    
    EXAMPLE: 
    ip ro add 192.168.42.0/24 via 172.23.0.2
   ``` 
   
6. Создать пользователей (ниже)

7. Для каждого созданного пользователя скопировать созданный сертификат из `./clients/` на 
клиента в директорию `/etc/openvpn/`, изменив расширение сертификата на `.conf`. 
Пример готового файла на роботе:
    
   ```
   /etc/openvpn/client.conf
   # service openvpn@client start   -   autoconnect on system startup
   ```
       
    
### Менеджмент пользователей 
___

Создать нового пользователя:
    
    sudo ./create_user.sh --name MB1 --ip 192.168.41.201

Удалить пользователя:
    
    sudo ./remove_user.sh --name MB1
    

Проверить существующие проброшенные порты

    sudo iptables -L -n -t nat    
    
