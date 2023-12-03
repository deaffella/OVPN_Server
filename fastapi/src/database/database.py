import os
import datetime
import psycopg2
import datetime
from typing import Dict, List, Tuple

import asyncpg
import asyncio






class Database_Sync():
    """
    Класс для взаимодействия с базой данных Postgres.
    """

    def __init__(self,
                 host:          str = os.getenv('POSTGRES_HOST'),
                 port:          str = os.getenv('POSTGRES_PORT'),
                 db_name:       str = os.getenv('POSTGRES_DB'),
                 user:          str = os.getenv('POSTGRES_USER'),
                 password:      str = os.getenv('POSTGRES_PASSWORD'),
                 check_tables:  bool = True):
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
        self.host = host
        self.port = port
        self.db_name = db_name
        self.user = user
        self.password = password
        self.check_tables = check_tables

        self.con_status = False
        self.connection = None


    def connect(self, verbose=False):
        """
        Подлкючиться к бд.
        :return:
        """
        try:
            self.connection = psycopg2.connect(host=self.host,
                                               port=self.port,
                                               database=self.db_name,
                                               user=self.user,
                                               password=self.password)
            self.con_status = True
            if verbose:
                print(f'\nDATABASE CONNECTION ESTABLISHED: {self.host}:{self.port}\n\n')
        except Exception as e:
            if verbose:
                print(f'\n\n\nCANT CONNECT TO DB: {self.host}:{self.port}\n\n')
            self.con_status = False

    def disconnect(self):
        """
        Отключиться от бд.
        :return:
        """
        try:
            self.con_status = False
            self.connection.close()
        except Exception as e:
            print(f"CAN'T DISCONNECT FROM DB: {self.host}:{self.port}\n\n'")

    def check_table_exist(self, table_name: str) -> bool:
        """
        Проверить существование таблицы внутри базы данных.
        :param table_name: Имя таблицы.
        :return:
        """
        sql_request = f"""SELECT EXISTS(
                        SELECT * 
                        FROM information_schema.tables 
                        WHERE 
                          table_schema = 'public' AND
                          table_name = '{table_name}');"""
        cur = self.connection.cursor()
        cur.execute(sql_request)
        table_exist = cur.fetchone()
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
            cur = self.connection.cursor()
            cur.execute(sql_request)
            self.connection.commit()
            if verbose:
                print("[OK]\tcreate table")
        except Exception as e:
            if verbose:
                print(f'[ERROR]\tcant create table:\n\n{sql_request}\n\n{e}')
            pass

    def __drop_table(self, table_name: str, verbose: bool = True):
        try:
            sql_request = f"DROP TABLE IF EXISTS public.{table_name}"
            cur = self.connection.cursor()
            cur.execute(sql_request)
            self.connection.commit()
            if verbose:
                print(f"[OK]\tdrop table {table_name}")
        except Exception as e:
            if verbose:
                print(f'[ERROR]\tcant drop table {table_name}\n{e}')
            pass

    def wipe_database(self, verbose: bool = True):
        self.__drop_table(table_name='certificates', verbose=verbose)
        self.__drop_table(table_name='ovpn_users', verbose=verbose)
        self.__drop_table(table_name='servers', verbose=verbose)
        # self.create_tables(verbose=verbose)

    def __create_servers_table(self, verbose: bool = False):
        """
        Создает таблицу для servers.
        :return:
        """
        sql_request = f"""
        CREATE TABLE IF NOT EXISTS public.servers
        (
            id bigserial,
            name character varying(255) NOT NULL UNIQUE,
            external_ip inet NOT NULL,
            external_port bigint NOT NULL UNIQUE,
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
            nickname character varying(255) NOT NULL UNIQUE,
            first_name character varying(255),
            last_name character varying,
            telegram_id bigint UNIQUE,
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
            ip inet NOT NULL UNIQUE,
            file_path character varying NOT NULL,
            creation_date timestamp with time zone NOT NULL,
            expiration_date timestamp with time zone NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT ovpn_user_id FOREIGN KEY (ovpn_user_id)
                REFERENCES public.ovpn_users (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
                NOT VALID,
            CONSTRAINT server_id FOREIGN KEY (server_id)
                REFERENCES public.servers (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
                NOT VALID
        );
        
        ALTER TABLE IF EXISTS public.users
            OWNER to {self.user};
        """
        self.__create__table(sql_request=sql_request, verbose=verbose)


    """SERVERS========================================================================================================"""
    def get_servers_list(self) -> List[Tuple[int, str, str, int, str, str, str, datetime.datetime, int]]:
        sql_request = (f"select id, name, external_ip, external_port, internal_ip, internal_port, "
                       f"internal_subnet, creation_date, monitor_port "
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
        try:
            cur = self.connection.cursor()
            cur.execute(sql_request)
        except Exception as e:
            raise e
        finally:
            self.connection.commit()
        result = cur.fetchall()
        return result

    def delete_server(self, server_id: int) -> Tuple[int, str, str, int, str, str, str, datetime.datetime, int]:
        sql_request = (f"DELETE from public.servers WHERE id = {server_id} "
                       f"RETURNING id, name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port;")
        try:
            cur = self.connection.cursor()
            cur.execute(sql_request)
        except Exception as e:
            raise e
        finally:
            self.connection.commit()
        result = cur.fetchall()
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
        try:
            cur = self.connection.cursor()
            cur.execute(sql_request)
        except Exception as e:
            raise e
        finally:
            self.connection.commit()
        result = cur.fetchall()
        return result

    def delete_ovpn_user(self, ovpn_user_id: int) -> Tuple[int, str, str, str, int, datetime.datetime]:
        sql_request = (f"DELETE from public.ovpn_users WHERE id = {ovpn_user_id} "
                       f"RETURNING id, nickname, first_name, last_name, telegram_id, registration_date;")
        try:
            cur = self.connection.cursor()
            cur.execute(sql_request)
        except Exception as e:
            raise e
        finally:
            self.connection.commit()
        result = cur.fetchall()
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
        try:
            cur = self.connection.cursor()
            cur.execute(sql_request)
        except Exception as e:
            raise e
        finally:
            self.connection.commit()
        result = cur.fetchall()
        return result

    def delete_certificate(self, certificate_id: int) -> Tuple[int, int, int, str, str, datetime.datetime, datetime.datetime]:
        sql_request = (f"DELETE from public.certificates WHERE id = {certificate_id} "
                       f"RETURNING id, server_id, ovpn_user_id, ip, file_path, "
                       f"creation_date, expiration_date;")
        try:
            cur = self.connection.cursor()
            cur.execute(sql_request)
        except Exception as e:
            raise e
        finally:
            self.connection.commit()
        result = cur.fetchall()
        return result




class Database_Async():
    """
    Класс для взаимодействия с базой данных Postgres.
    """

    def __init__(self,
                 host:          str = os.getenv('POSTGRES_HOST'),
                 port:          str = os.getenv('POSTGRES_PORT'),
                 db_name:       str = os.getenv('POSTGRES_DB'),
                 user:          str = os.getenv('POSTGRES_USER'),
                 password:      str = os.getenv('POSTGRES_PASSWORD'),
                 ):
        """
        Инициализирует клиент базы данных.
        :param ip:        Адрес бд.
        :param port:      Порт бд.
        :param db_name:      Имя бд.
        :param user:      Имя пользователя.
        :param password:  Пароль.
        """
        self.host = host
        self.port = port
        self.db_name = db_name
        self.user = user
        self.password = password

        self.con_status = False
        self.connection = None


    async def connect(self, verbose=False):
        """
        Подлкючиться к бд.
        :return:
        """
        try:
            self.connection: asyncpg.Connection = await asyncpg.connect(host=self.host,
                                                                        port=self.port,
                                                                        database=self.db_name,
                                                                        user=self.user,
                                                                        password=self.password)

            self.con_status = True
            if verbose:
                print(f'\nDATABASE CONNECTION ESTABLISHED: {self.host}:{self.port}\n\n')
        except Exception as e:
            if verbose:
                print(f'\n\n\nCANT CONNECT TO DB: {self.host}:{self.port}\n\n')
            self.con_status = False

    async def disconnect(self):
        """
        Отключиться от бд.
        :return:
        """
        try:
            self.con_status = False
            await self.connection.close()
        except Exception as e:
            print(f"CAN'T DISCONNECT FROM DB: {self.host}:{self.port}\n\n'")

    async def check_table_exist(self, table_name: str) -> bool:
        """
        Проверить существование таблицы внутри базы данных.
        :param table_name: Имя таблицы.
        :return:
        """
        sql_request = f"""SELECT EXISTS(
                        SELECT * 
                        FROM information_schema.tables 
                        WHERE 
                          table_schema = 'public' AND
                          table_name = '{table_name}');"""
        return bool(await self.connection.fetchval(sql_request))

    async def create_tables(self, verbose: bool = True):
        """
        Создать необходимые таблицы
        :return:
        """
        try:
            await self.__create_servers_table(verbose=verbose)
            await self.__create_ovpn_users_table(verbose=verbose)
            await self.__create_certificates_table(verbose=verbose)

            if verbose:
                print("[OK]\tall tables exist")
        except Exception as e:
            if verbose:
                print(f'[ERROR]\tошибка в функции создания таблиц!\n{e}')
            pass

    async def __create__table(self, sql_request: str, verbose: bool = False):
        """
        Создает таблицу по запросу.
        :return:
        """
        try:
            await self.connection.execute(sql_request)
            if verbose:
                print("[OK]\tcreate table")
        except Exception as e:
            if verbose:
                print(f'[ERROR]\tcant create table:\n\n{sql_request}\n\n{e}')
            pass

    async def __drop_table(self, table_name: str, verbose: bool = True):
        try:
            sql_request = f"DROP TABLE IF EXISTS public.{table_name}"
            await self.connection.execute(sql_request)
            if verbose:
                print(f"[OK]\tdrop table {table_name}")
        except Exception as e:
            if verbose:
                print(f'[ERROR]\tcant drop table {table_name}\n{e}')
            pass

    async def wipe_database(self, verbose: bool = True):
        await self.__drop_table(table_name='certificates', verbose=verbose)
        await self.__drop_table(table_name='ovpn_users', verbose=verbose)
        await self.__drop_table(table_name='servers', verbose=verbose)
        #await self.create_tables(verbose=verbose)

    async def __create_servers_table(self, verbose: bool = True):
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
            country character varying(255),
            PRIMARY KEY (id)
        );

        ALTER TABLE IF EXISTS public.servers
            OWNER to {self.user};
        """
        await self.__create__table(sql_request=sql_request, verbose=verbose)

    async def __create_ovpn_users_table(self, verbose: bool = True):
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
        await self.__create__table(sql_request=sql_request, verbose=verbose)

    async def __create_certificates_table(self, verbose: bool = True):
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
                ON DELETE CASCADE
                NOT VALID,
            CONSTRAINT server_id FOREIGN KEY (server_id)
                REFERENCES public.servers (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
                NOT VALID
        );
        
        ALTER TABLE IF EXISTS public.users
            OWNER to {self.user};
        """
        await self.__create__table(sql_request=sql_request, verbose=verbose)


    """SERVERS========================================================================================================"""
    async def get_servers_list(self) -> List[Tuple[int, str, str, int, str, str, str, datetime.datetime, int, str]]:
        sql_request = (f"select (id, name, external_ip, external_port, internal_ip, internal_port, "
                       f"internal_subnet, creation_date, monitor_port, country) "
                       f"from public.servers order by id ASC")
        records = await self.connection.fetch(sql_request)
        return [dict(record)['row'] for record in records]

    async def add_server(self,
                   name: str,
                   external_ip: str,
                   external_port: int,
                   internal_ip: str,
                   internal_port: int,
                   internal_subnet: str,
                   creation_date: datetime.datetime,
                   monitor_port: int = 4401,
                   country: str = "") -> Tuple[int, str, str, int, str, str, str, datetime.datetime, int, str]:
        sql_request = (f"insert into public.servers (name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port, country) "
                       f"values ('{name}', '{external_ip}', '{external_port}', '{internal_ip}', "
                       f"'{internal_port}', '{internal_subnet}', '{creation_date}', {monitor_port}, '{country}') "
                       f"RETURNING id, name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port, country;")
        records = await self.connection.fetch(sql_request)
        return [tuple(record) for record in records][0]


    async def delete_server(self, server_id: int) -> Tuple[int, str, str, int, str, str, str, datetime.datetime, int, str]:
        sql_request = (f"DELETE from public.servers WHERE id = {server_id} "
                       f"RETURNING id, name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port, country;")
        records = await self.connection.fetch(sql_request)
        return [tuple(record) for record in records][0]


    """USERS========================================================================================================"""
    async def get_ovpn_users_list(self) -> List[Tuple[int, str, str, str, int, datetime.datetime]]:
        sql_request = (f"select (id, nickname, first_name, last_name, telegram_id, registration_date) "
                       f"from public.ovpn_users order by id ASC;")
        records = await self.connection.fetch(sql_request)
        return [dict(record)['row'] for record in records]

    async def add_ovpn_user(self,
                      nickname: str,
                      registration_date: datetime.datetime,
                      first_name: str = None,
                      last_name: str = None,
                      telegram_id: int = None) -> Tuple[int, str, str, str, int,datetime.datetime]:
        sql_request = (f"insert into public.ovpn_users (nickname, first_name, last_name, telegram_id, registration_date) "
                       f"values ('{nickname}', '{first_name}', '{last_name}', '{telegram_id}', '{registration_date}') "
                       f"RETURNING id, nickname, first_name, last_name, telegram_id, registration_date")
        records = await self.connection.fetch(sql_request)
        return [tuple(record) for record in records][0]

    async def delete_ovpn_user(self, ovpn_user_id: int) -> Tuple[int, str, str, str, int, datetime.datetime]:
        sql_request = (f"DELETE from public.ovpn_users WHERE id = {ovpn_user_id} "
                       f"RETURNING id, nickname, first_name, last_name, telegram_id, registration_date;")
        records = await self.connection.fetch(sql_request)
        return [tuple(record) for record in records][0]


    """CERTIFICATES========================================================================================================"""
    async def get_certificates_list(self) -> List[Tuple[int, int, int, str, str, datetime.datetime, datetime.datetime]]:
        sql_request = (f"select (id, server_id, ovpn_user_id, ip, file_path, creation_date, expiration_date) "
                       f"from public.certificates order by id ASC;")
        records = await self.connection.fetch(sql_request)
        return [dict(record)['row'] for record in records]

    async def add_certificate(self,
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
        records = await self.connection.fetch(sql_request)
        return [tuple(record) for record in records][0]

    async def delete_certificate(self, certificate_id: int) -> Tuple[int, int, int, str, str, datetime.datetime, datetime.datetime]:
        sql_request = (f"DELETE from public.certificates WHERE id = {certificate_id} "
                       f"RETURNING id, server_id, ovpn_user_id, ip, file_path, "
                       f"creation_date, expiration_date;")
        records = await self.connection.fetch(sql_request)
        return [tuple(record) for record in records][0]




if __name__ == '__main__':
    async def main():
        db = Database()
        await db.connect()
        await db.create_tables()
        await db.wipe_database()

        print('servers', await db.get_servers_list())
        print()
        # print('add', await db.add_server(name='test_1', external_ip='8.8.8.8', external_port=1194, internal_ip='192.168.11.1', internal_port=1194, internal_subnet='192.168.33.0', creation_date=datetime.datetime.now(), monitor_port=4401, country="RU"))
        print()
        # print('delete', await db.delete_server(server_id=8))
        # print()
        # print('servers', await db.get_servers_list())
        print()

        print('users', await db.get_ovpn_users_list())
        print()
        print('add',
              await db.add_ovpn_user(nickname='user_1', registration_date=datetime.datetime.now(), first_name=None,
                                     last_name=None, telegram_id=111))
        print()
        print('delete', await db.delete_ovpn_user(ovpn_user_id=1))
        print()
        print('users', await db.get_ovpn_users_list())
        print()

        print('certificates', await db.get_certificates_list())
        print()
        print('add', await db.add_certificate(server_id=9, ovpn_user_id=1, ip='192.168.22.22', file_path='/qwe/qwe',
                                              creation_date=datetime.datetime.now(),
                                              expiration_date=datetime.datetime.now()))
        print('add', await db.add_certificate(server_id=9, ovpn_user_id=1, ip='192.168.22.11', file_path='/qwe/qwe',
                                              creation_date=datetime.datetime.now(),
                                              expiration_date=datetime.datetime.now()))
        print()
        print('delete', await db.delete_certificate(certificate_id=2))
        print('delete', await db.delete_certificate(certificate_id=3))
        print()
        print('certificates', await db.get_certificates_list())
        print()

        await db.disconnect()


    asyncio.run(main())
