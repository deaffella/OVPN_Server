### Первоначальная настройка 
___

1. Клонировать проект.

2. Изменить `DEFAULT SUBNET`, `DEFAULT KEY NAME`, `DEFAULT CRT NAME`
внутри `server/custom_config/openvpn.conf`:

  
   Пример:

   ```
   server 192.168.42.0 255.255.255.0                   # Заменить `__SUBNET` на внутреннюю подсеть
   key /etc/openvpn/pki/private/default_priv_key.key   # Изменить имя ключа на `внешний_ip.key`
   cert /etc/openvpn/pki/issued/default_cert.crt       # Изменить имя cертификата на `внешний_ip.key`
   ```

3. Изменить `OVPN_CN`, `OVPN_SERVER`, `OVPN_SERVER_URL` внутри `server/custom_config/ovpn_env.sh`.

  
   Пример:

   ```
   declare -x OVPN_CN=217.144.98.104
   declare -x OVPN_SERVER=192.168.42.0/24             # CHANGE DEFAULT SUBNET
   declare -x OVPN_SERVER_URL=udp://217.144.98.104    # CHANGE EXTERNAL IP
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
    
