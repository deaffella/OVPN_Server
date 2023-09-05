# OVPN_Server
___

## Первоначальная настройка 
___

1. Клонировать проект.

   ```bash
   git@gitlab.smart-glow.ru:course_robots/OVPN_Server.git
   ```

2. Перейти в папку `OVPN_Server/ovpn/custom_config` и изменить конфигурацию сервера
с помощью скрипта `MAKE_CONFIG.sh`. В ходе конфигурирования скрипта потребуется несколько 
раз ввести passphrase для easy-rsa.

   ```bash
   sudo bash MAKE_CONFIG.sh --subnet 192.168.42.0 --mask 24
   
   # Для автоматического определения `ext_ip` можно воспользоваться командой:
   curl -s http://whatismijnip.nl |cut -d " " -f 5
   ```
   
3. Перейти в папку `OVPN_Server/telegram_bot` и создать два файла с настройками для 
телеграм бота:

   ```bash
   # Токен для телеграм бота
   echo "TOKEN=токен_от_телеграм_бота > token.env.secret"
   
   # Список авторизованных пользователей телеграм бота с содержанием вида: 
   # {
   #  "0": {
   #    "name": "some_tg_username",
   #    "id":   "269796099"
   #  }
   # }
   nano tg_users.json.secret   
   ```

4. Вернуться в главную директорию `OVPN_Server`, указать правильную подсеть 
внутри скрипта `build_project.sh` (по дефолту используется `192.168.42.0/24`) 
и поднять проект:

   ```bash
   sudo bash build_project.sh
   ```


## Ручная загрузка созданного сертификата на клиента (deprecaded)
___

Для каждого созданного пользователя скопировать созданный сертификат из `OVPN_Server/ovpn/custom_config/config/ccd/` на 
клиента в директорию `/etc/openvpn/`, изменив расширение сертификата на `.conf`. 
Пример готового файла на роботе:
    
   ```bash
   /etc/openvpn/client.conf
   # service openvpn@client start   -   autoconnect on system startup
   ```
       
    
### Менеджмент пользователей (deprecaded)
___

Создать нового пользователя:
    
   ```bash
   # OVPN_Server/ovpn/server_management/
    sudo ./create_user.sh --name MB1 --ip 192.168.42.201
   ```

Удалить пользователя:
    
   ```bash
   # OVPN_Server/ovpn/server_management/
    sudo ./remove_user.sh --name MB1
   ```

Проверить существующие проброшенные порты:
    
   ```bash
   # OVPN_Server/ovpn/server_management/
    sudo iptables -L -n -t nat
   ```


## Возможные проблемы
___

1. Если после подключения клиента к серверу пинг с клиента проходит 
до сервера, но не проходит до `8.8.8.8` (нет интернета, страницы не грузятся), 
то могут помочь следующие команды (вводить на клиенте):

   ```bash
   # подсказка от chatgpt
   sudo iptables -t nat -A POSTROUTING -s 192.168.42.0/24 -o eth0 -j MASQUERADE

   # восстановление iptables из бэкапа
   cd ovpn/server_management && sudo bash iptables_restore.sh

   # использование последней команды из скрипта выше
   sudo iptables -A FORWARD -i eth0 -j ACCEPT
   ```

___

2. При подключении главного сервера с rabbitmq в качестве клиента к vpn сети 
возможно возникновение ситуации, когда главный сервер становится недоступен по белому 
статическому ip-адресу, но остается доступен внутри vpn сети. Данная проблема возникает 
из-за изменения стандартного сетевого маршрута на клиенте после подключения к vpn. 
Для того чтобы стандартный сетевой маршрут не изменялся после подключения к vpn, 
необходимо внутри клиентского vpn сертификата удалить\закомментировать строку 
`redirect-gateway def1`.
Проверить сетевые маршруты можно с помощью команды `ip ro`:

   ```bash
   root@main-rmq-server:~# ip ro
   default via 46.254.21.254 dev eth0 proto static            # стандартный сетевой маршрут
   ...
   46.254.20.0/23 dev eth0 proto kernel scope link src 46.254.20.122
   172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1
   ```
   
   

   