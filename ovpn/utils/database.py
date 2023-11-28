import os
import sys
import time
import datetime
import psycopg2

import datetime

from typing import Dict, List, Tuple


class Database():
    """
    Класс для взаимодействия с базой данных Postgres.
    """

    def __init__(self,
                 ip:            str = os.getenv('POSTGRES_HOST'),
                 port:          str = os.getenv('POSTGRES_PORT'),
                 db_name:       str = os.getenv('POSTGRES_DB'),
                 user:          str = os.getenv('POSTGRES_USER'),
                 password:      str = os.getenv('POSTGRES_PASSWORD'),
                 check_tables:  bool = True,
                 verbose:       bool = False):
        """
        Инициализирует клиент базы данных.
        :param ip:        Адрес бд.
        :param port:      Порт бд.
        :param db_name:      Имя бд.
        :param user:      Имя пользователя.
        :param password:  Пароль.
        :param check_tables: Если True, проверяет наличие таблиц и создает их в случае их отсутствия.
        :param verbose:      Если True, принтует логи о выполнении команд.
        """
        self.ip = ip
        self.port = port
        self.db_name = db_name
        self.user = user
        self.password = password
        self.check_tables = check_tables

        self.con_status = False

        self.connection = self.connect()
        if self.check_tables:
            self.create_tables(verbose=verbose)


    def connect(self, verbose=False):
        """
        Подлкючиться к бд.
        :return:
        """
        try:
            connection = psycopg2.connect(host=self.ip,
                                          port=self.port,
                                          database=self.db_name,
                                          user=self.user,
                                          password=self.password)
            self.con_status = True
            if verbose:
                print(f'\nDATABASE CONNECTION ESTABLISHED: {self.ip}:{self.port}\n\n')

            self.connection = connection
            return self.connection
        except Exception as e:
            if verbose:
                print(f'\n\n\nCANT CONNECT TO DB: {self.ip}:{self.port}\n\n')
            self.con_status = False
            return False

    def disconnect(self):
        """
        Отключиться от бд.
        :return:
        """
        try:
            self.con_status = False
            self.connection.close()
            # print('\nDATABASE DISCONNECTED: {}:{}\n\n'.format(self.db_ip,
            #                                                   self.db_port))
        except Exception as e:
            print(f"CAN'T DISCONNECT FROM DB: {self.ip}:{self.port}\n\n'")

    def check_table_exist(self, table_name: str) -> bool:
        """
        Проверить существование таблицы внутри базы данных.
        :param table_name: Имя таблицы.
        :return:
        """
        self.connect()
        sql_request = f"""SELECT EXISTS(
                        SELECT * 
                        FROM information_schema.tables 
                        WHERE 
                          table_schema = 'public' AND
                          table_name = '{table_name}');"""
        cur = self.connection.cursor()
        cur.execute(sql_request)
        table_exist = cur.fetchone()
        self.disconnect()
        return table_exist[0]

    def create_tables(self, verbose: bool = False):
        """
        Создать необходимые таблицы
        :return:
        """
        try:
            self.__create_servers_table(verbose=verbose)
            self.__create_ovpn_users_table(verbose=verbose)
            self.__create_certificates_table(verbose=verbose)

            if verbose:
                print("[OK]\tall tables exist")
        except Exception as e:
            if verbose:
                print(f'[ERROR]\tошибка в функции создания таблиц!\n{e}')
            pass

    def __create__table(self, sql_request: str, verbose: bool = False):
        """
        Создает таблицу по запросу.
        :return:
        """
        try:
            #self.connect()
            cur = self.connection.cursor()
            cur.execute(sql_request)
            self.connection.commit()
            #self.disconnect()

            if verbose:
                print("[OK]\tcreate table")
        except Exception as e:
            if verbose:
                print(f'[ERROR]\tcant create table:\n\n{sql_request}\n\n{e}')
            pass

    def __drop_table(self, table_name: str, verbose: bool = True):
        try:
            self.connect()
            sql_request = f"DROP TABLE IF EXISTS public.{table_name}"
            cur = self.connection.cursor()
            cur.execute(sql_request)
            self.connection.commit()
            self.disconnect()

            if verbose:
                print(f"[OK]\tdrop table {table_name}")
        except Exception as e:

            if verbose:
                print(f'[ERROR]\tcant drop table {table_name}\n{e}')
            pass

    def wipe_database(self, verbose: bool = True):
        # self.__drop_table(table_name='features', verbose=verbose)
        # self.__drop_table(table_name='images', verbose=verbose)
        # self.__drop_table(table_name='persons', verbose=verbose)
        self.create_tables(verbose=verbose)


    def __create_servers_table(self, verbose: bool = False):
        """
        Создает таблицу для servers.
        :return:
        """
        sql_request = f"""
        CREATE TABLE IF NOT EXISTS public.servers
        (
            id bigserial,
            name character varying(255) NOT NULL,
            external_ip inet NOT NULL,
            external_port bigint NOT NULL,
            internal_ip inet NOT NULL,
            internal_port bigint DEFAULT 1194,
            internal_subnet inet NOT NULL,
            creation_date timestamp with time zone NOT NULL,
            monitor_port bigint DEFAULT 4401,
            PRIMARY KEY (id)
        );

        ALTER TABLE IF EXISTS public.servers
            OWNER to {self.user};
        """
        self.__create__table(sql_request=sql_request, verbose=verbose)

    def __create_ovpn_users_table(self, verbose: bool = False):
        """
        Создает таблицу для users.
        :return:
        """
        sql_request = f"""
        CREATE TABLE IF NOT EXISTS public.ovpn_users
        (
            id bigserial,
            nickname character varying(255) NOT NULL,
            first_name character varying(255),
            last_name character varying,
            telegram_id bigint,
            registration_date timestamp with time zone NOT NULL,
            PRIMARY KEY (id)
        );
        
        ALTER TABLE IF EXISTS public.ovpn_users
            OWNER to {self.user};
        """
        self.__create__table(sql_request=sql_request, verbose=verbose)

    def __create_certificates_table(self, verbose: bool = False):
        """
        Создает таблицу для certificates.
        :return:
        """
        sql_request = f"""
        CREATE TABLE IF NOT EXISTS public.certificates
        (
            id bigserial,
            server_id bigint NOT NULL,
            ovpn_user_id bigint NOT NULL,
            ip inet NOT NULL,
            file_path character varying NOT NULL,
            creation_date timestamp with time zone NOT NULL,
            expiration_date timestamp with time zone NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT ovpn_user_id FOREIGN KEY (ovpn_user_id)
                REFERENCES public.ovpn_users (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
                NOT VALID,
            CONSTRAINT server_id FOREIGN KEY (server_id)
                REFERENCES public.servers (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
                NOT VALID
        );
        
        ALTER TABLE IF EXISTS public.users
            OWNER to {self.user};
        """
        self.__create__table(sql_request=sql_request, verbose=verbose)


    """SERVERS========================================================================================================"""
    def get_servers_list(self) -> List[Tuple[int, str, str, int, str, str, str, datetime.datetime, int]]:
        sql_request = (f"select (id, name, external_ip, external_port, internal_ip, internal_port, "
                       f"internal_subnet, creation_date, monitor_port) "
                       f"from public.servers order by id ASC")
        cur = self.connection.cursor()
        cur.execute(sql_request)
        result = cur.fetchall()
        return result

    def add_server(self,
                   name: str,
                   external_ip: str,
                   external_port: int,
                   internal_ip: str,
                   internal_port: int,
                   internal_subnet: str,
                   creation_date: datetime.datetime,
                   monitor_port: int = 4401) -> Tuple[int, str, str, int, str, str, str, datetime.datetime, int]:
        sql_request = (f"insert into public.servers (name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port) "
                       f"values ('{name}', '{external_ip}', '{external_port}', '{internal_ip}', "
                       f"'{internal_port}', '{internal_subnet}', '{creation_date}', {monitor_port}) "
                       f"RETURNING id, name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port;")
        cur = self.connection.cursor()
        result = cur.execute(sql_request)
        self.connection.commit()
        return result

    def delete_server(self, server_id: int) -> Tuple[int, str, str, int, str, str, str, datetime.datetime, int]:
        sql_request = (f"DELETE from public.servers WHERE id = {server_id} "
                       f"RETURNING id, name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port;")
        cur = self.connection.cursor()
        result = cur.execute(sql_request)
        self.connection.commit()
        return result


    """USERS========================================================================================================"""
    def get_ovpn_users_list(self) -> List[Tuple[int, str, str, str, int, datetime.datetime]]:
        sql_request = (f"select id, nickname, first_name, last_name, telegram_id, registration_date "
                       f"from public.ovpn_users order by id ASC;")
        cur = self.connection.cursor()
        cur.execute(sql_request)
        result = cur.fetchall()
        return result

    def add_ovpn_user(self,
                      nickname: str,
                      registration_date: datetime.datetime,
                      first_name: str = None,
                      last_name: str = None,
                      telegram_id: int = None) -> Tuple[int, str, str, str, int,datetime.datetime]:
        sql_request = (f"insert into public.ovpn_users (nickname, first_name, last_name, telegram_id, registration_date) "
                       f"values ('{nickname}', '{first_name}', '{last_name}', '{telegram_id}', '{registration_date}') "
                       f"RETURNING id, nickname, first_name, last_name, telegram_id, registration_date")
        cur = self.connection.cursor()
        result = cur.execute(sql_request)
        self.connection.commit()
        return result

    def delete_ovpn_user(self, ovpn_user_id: int) -> Tuple[int, str, str, str, int, datetime.datetime]:
        sql_request = (f"DELETE from public.ovpn_users WHERE id = {ovpn_user_id} "
                       f"RETURNING id, nickname, first_name, last_name, telegram_id, registration_date;")
        cur = self.connection.cursor()
        result = cur.execute(sql_request)
        self.connection.commit()
        return result


    """CERTIFICATES========================================================================================================"""
    def get_certificates_list(self) -> List[Tuple[int, int, int, str, str, datetime.datetime, datetime.datetime]]:
        sql_request = (f"select id, server_id, ovpn_user_id, ip, file_path, creation_date, expiration_date "
                       f"from public.certificates order by id ASC;")
        cur = self.connection.cursor()
        cur.execute(sql_request)
        result = cur.fetchall()
        return result

    def add_certificate(self,
                        server_id: int,
                        ovpn_user_id: int,
                        ip: str,
                        file_path: str,
                        creation_date: datetime.datetime,
                        expiration_date: datetime.datetime) -> Tuple[int, int, int, str, str,
                                                                     datetime.datetime, datetime.datetime]:
        sql_request = (f"insert into public.certificates (server_id, ovpn_user_id, ip, file_path, "
                       f"creation_date, expiration_date) "
                       f"values ('{server_id}', '{ovpn_user_id}', '{ip}', '{file_path}', '{creation_date}', "
                       f"'{expiration_date}') "
                       f"RETURNING id, server_id, ovpn_user_id, ip, file_path, "
                       f"creation_date, expiration_date;")
        cur = self.connection.cursor()
        result = cur.execute(sql_request)
        self.connection.commit()
        return result

    def delete_certificate(self, certificate_id: int) -> Tuple[int, int, int, str, str, datetime.datetime, datetime.datetime]:
        sql_request = (f"DELETE from public.certificates WHERE id = {certificate_id} "
                       f"RETURNING id, server_id, ovpn_user_id, ip, file_path, "
                       f"creation_date, expiration_date;")
        cur = self.connection.cursor()
        result = cur.execute(sql_request)
        self.connection.commit()
        return result




if __name__ == '__main__':
    db = Database(verbose=True)

    # print()
    # print('servers', db.get_servers_list())
    # print(db.add_server(name='test_1', external_ip='8.8.8.8', external_port=1194, internal_ip='192.168.11.1', internal_port=1194, internal_subnet='192.168.33.0', creation_date=datetime.datetime.now(), monitor_port=4401))
    # print(db.add_server(name='test_2', external_ip='8.8.8.8', external_port=1194, internal_ip='192.168.22.1', internal_port=1194, internal_subnet='192.168.33.0', creation_date=datetime.datetime.now(), monitor_port=4401))
    # print('servers', db.get_servers_list())
    # print()
    # print(db.delete_server(server_id=1))
    # print(db.get_servers_list())
    # print()
    # print()

    # print()
    # print('ovpn_users', db.get_ovpn_users_list())
    # print(db.add_ovpn_user(nickname='user_1', registration_date=datetime.datetime.now(), first_name=None, last_name=None, telegram_id=111))
    # print(db.add_ovpn_user(nickname='user_2', registration_date=datetime.datetime.now(), first_name=None, last_name=None, telegram_id=222))
    # print('ovpn_users', db.get_ovpn_users_list())
    # print()
    # print(db.delete_ovpn_user(ovpn_user_id=1))
    # print('ovpn_users', db.get_ovpn_users_list())
    # print()
    # print()

    # print()
    # print('certificates', db.get_certificates_list())
    # print(db.add_certificate(server_id=2, ovpn_user_id=2, ip='192.168.22.11', file_path='/asd/asd', creation_date=datetime.datetime.now(), expiration_date=datetime.datetime.now()))
    # print(db.add_certificate(server_id=2, ovpn_user_id=2, ip='192.168.22.22', file_path='/qwe/qwe', creation_date=datetime.datetime.now(), expiration_date=datetime.datetime.now()))
    # print('certificates', db.get_certificates_list())
    # print()
    # print(db.delete_certificate(certificate_id=1))
    # print('certificates', db.get_certificates_list())
    # print()
    # print()
