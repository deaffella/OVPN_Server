from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, close_all_sessions
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.sql import text

import typing
import datetime

class Base(DeclarativeBase):
    pass


class DBEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not DBEngine._instance:
            DBEngine._instance = super(DBEngine, cls).__new__(cls, *args, **kwargs)
        return DBEngine._instance

    async def start_up(self, db_connection_string: str):
        connection_prams = {
            'future': True,
            'echo': False,
            'echo_pool': False,
            'poolclass': AsyncAdaptedQueuePool,
            'pool_size': 1,
            'max_overflow': 0
        }
        self.engine = create_async_engine(
            db_connection_string,
            **connection_prams
        )
        await self._get_session()

    async def _get_session(self):
        async_session = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        async with async_session() as session:
            try:
                return session
            finally:
                await session.close()

    async def init_models(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def get_session():
        return await DBEngine()._get_session()

    @staticmethod
    async def close_database_connection():
        close_all_sessions()
        await DBEngine().engine.dispose()

    @staticmethod
    async def startup(host: str, port: str, user: str, password: str, db: str):
        DBEngine.host = host
        DBEngine.port = port
        DBEngine.user = user
        DBEngine.password = password
        DBEngine.db = db
        db_connection_string = f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}'
        await DBEngine().start_up(db_connection_string)

    @staticmethod
    async def drop_table(session, table: str) -> None:
        query = text(f'DROP TABLE IF EXISTS public.{table} CASCADE;')
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def check_table_exist(session,
                                table_name: str) -> bool:
        query = text(f"""SELECT EXISTS(SELECT * FROM information_schema.tables WHERE
                  table_schema = 'public' AND
                  table_name = '{table_name}');""")
        async_result = await session.execute(query)
        result = async_result.fetchone()[0]
        return result

    @staticmethod
    async def create_tables(session):
        """
        Создать необходимые таблицы
        :return:
        """
        try:
            await DBEngine.__create_servers_table(session=session)
            await DBEngine.__create_ovpn_users_table(session=session)
            await DBEngine.__create_certificates_table(session=session)
            print('[OK]\t all tables exist!')
        except Exception as e:
            print(f'[ERROR]\tошибка в функции создания таблиц!\n{e}')

    @staticmethod
    async def __create_servers_table(session):
        """
        Создает таблицу для servers.
        :return:
        """
        await session.execute(text(f"CREATE TABLE IF NOT EXISTS public.servers (id bigserial,"
                                   f"name character varying(255) NOT NULL,"
                                   f"external_ip inet NOT NULL,"
                                   f"external_port bigint NOT NULL,"
                                   f"internal_ip inet NOT NULL,"
                                   f"internal_port bigint DEFAULT 1194,"
                                   f"internal_subnet inet NOT NULL,"
                                   f"creation_date timestamp with time zone NOT NULL,"
                                   f"monitor_port bigint DEFAULT 4401,"
                                   f"country character varying(255),"
                                   f"PRIMARY KEY (id));"))
        await session.execute(text(f"ALTER TABLE IF EXISTS public.servers "
                                   f"OWNER to {DBEngine.user};"))
        await session.commit()

    @staticmethod
    async def __create_ovpn_users_table(session):
        """
        Создает таблицу для users.
        :return:
        """
        await session.execute(text(f"CREATE TABLE IF NOT EXISTS public.ovpn_users"
                                   f"(id bigserial, nickname character varying(255) NOT NULL,"
                                   f"first_name character varying(255), last_name character varying, "
                                   f"telegram_id bigint, registration_date timestamp with time zone NOT NULL,"
                                   f"PRIMARY KEY (id));"))
        await session.execute(text(f"ALTER TABLE IF EXISTS public.ovpn_users "
                                   f"OWNER to {DBEngine.user};"))
        await session.commit()



    @staticmethod
    async def __create_certificates_table(session):
        """
        Создает таблицу для certificates.
        :return:
        """
        await session.execute(text(f"CREATE TABLE IF NOT EXISTS public.certificates (id bigserial,"
                                   f"server_id bigint NOT NULL, ovpn_user_id bigint NOT NULL,"
                                   f"ip inet NOT NULL, file_path character varying NOT NULL, "
                                   f"creation_date timestamp with time zone NOT NULL, "
                                   f"expiration_date timestamp with time zone NOT NULL, "
                                   f"PRIMARY KEY (id), "
                                   f"CONSTRAINT ovpn_user_id FOREIGN KEY (ovpn_user_id) "
                                   f"REFERENCES public.ovpn_users (id) MATCH SIMPLE "
                                   f"ON UPDATE NO ACTION "
                                   f"ON DELETE NO ACTION NOT VALID, "
                                   f"CONSTRAINT server_id FOREIGN KEY (server_id) "
                                   f"REFERENCES public.servers (id) MATCH SIMPLE "
                                   f"ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID);"))
        await session.execute(text(f"ALTER TABLE IF EXISTS public.certificates "
                                   f"OWNER to {DBEngine.user};"))
        await session.commit()


    """SERVERS========================================================================================================"""

    @staticmethod
    async def get_servers_list(session) -> typing.List[typing.Tuple[int, str, str, int, str, str, str, datetime.datetime, int, str]]:
        sql_request = (f"select (id, name, external_ip, external_port, internal_ip, internal_port, "
                       f"internal_subnet, creation_date, monitor_port, country) "
                       f"from public.servers order by id ASC")
        records = await session.execute(text(sql_request))
        return [dict(record)['row'] for record in records]

    # @staticmethod
    # async def get_server_by_id(session, id: int) -> typing.List[typing.Tuple[int, str, str, int, str, str, str, datetime.datetime, int, str]]:
    #     sql_request = (f"select (id, name, external_ip, external_port, internal_ip, internal_port, "
    #                    f"internal_subnet, creation_date, monitor_port, country) "
    #                    f"from public.servers order by id ASC where id={id}")
    #     records = await session.execute(text(sql_request))
    #     return [dict(record)['row'] for record in records]

    @staticmethod
    async def add_server(session,
                         name: str,
                         external_ip: str,
                         external_port: int,
                         internal_ip: str,
                         internal_port: int,
                         internal_subnet: str,
                         creation_date: datetime.datetime,
                         monitor_port: int = 4401,
                         country: str = "") -> typing.Tuple[int, str, str, int, str, str, str, datetime.datetime, int, str]:
        sql_request = (f"insert into public.servers (name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port, country) "
                       f"values ('{name}', '{external_ip}', '{external_port}', '{internal_ip}', "
                       f"'{internal_port}', '{internal_subnet}', '{creation_date}', {monitor_port}, '{country}') "
                       f"RETURNING id, name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port, country;")
        records = await session.execute(text(sql_request))
        return [tuple(record) for record in records][0]

    @staticmethod
    async def delete_server(session, server_id: int) -> typing.Tuple[
        int, str, str, int, str, str, str, datetime.datetime, int, str]:
        sql_request = (f"DELETE from public.servers WHERE id = {server_id} "
                       f"RETURNING id, name, external_ip, external_port, internal_ip, "
                       f"internal_port, internal_subnet, creation_date, monitor_port, country;")
        records = await session.execute(text(sql_request))
        return [tuple(record) for record in records][0]

    """USERS========================================================================================================"""

    @staticmethod
    async def get_ovpn_users_list(session) -> typing.List[typing.Tuple[int, str, str, str, int, datetime.datetime]]:
        sql_request = (f"select (id, nickname, first_name, last_name, telegram_id, registration_date) "
                       f"from public.ovpn_users order by id ASC;")
        records = await session.execute(text(sql_request))
        return [dict(record)['row'] for record in records]

    @staticmethod
    async def add_ovpn_user(session,
                            nickname: str,
                            registration_date: datetime.datetime,
                            first_name: str = None,
                            last_name: str = None,
                            telegram_id: int = None) -> typing.Tuple[int, str, str, str, int, datetime.datetime]:
        sql_request = (f"insert into public.ovpn_users (nickname, first_name, last_name, telegram_id, registration_date) "
            f"values ('{nickname}', '{first_name}', '{last_name}', '{telegram_id}', '{registration_date}') "
            f"RETURNING id, nickname, first_name, last_name, telegram_id, registration_date")
        records = await session.connection.execute(text(sql_request))
        return [tuple(record) for record in records][0]

    @staticmethod
    async def delete_ovpn_user(session, ovpn_user_id: int) -> typing.Tuple[int, str, str, str, int, datetime.datetime]:
        sql_request = (f"DELETE from public.ovpn_users WHERE id = {ovpn_user_id} "
                       f"RETURNING id, nickname, first_name, last_name, telegram_id, registration_date;")
        records = await session.connection.execute(text(sql_request))
        return [tuple(record) for record in records][0]

    """CERTIFICATES========================================================================================================"""

    @staticmethod
    async def get_certificates_list(session) -> typing.List[typing.Tuple[int, int, int, str, str, datetime.datetime, datetime.datetime]]:
        sql_request = (f"select (id, server_id, ovpn_user_id, ip, file_path, creation_date, expiration_date) "
                       f"from public.certificates order by id ASC;")
        records = await session.execute(text(sql_request))
        return [dict(record)['row'] for record in records]

    @staticmethod
    async def add_certificate(session,
                              server_id: int,
                              ovpn_user_id: int,
                              ip: str,
                              file_path: str,
                              creation_date: datetime.datetime,
                              expiration_date: datetime.datetime) -> typing.Tuple[int, int, int, str, str,
    datetime.datetime, datetime.datetime]:
        sql_request = (f"insert into public.certificates (server_id, ovpn_user_id, ip, file_path, "
                       f"creation_date, expiration_date) "
                       f"values ('{server_id}', '{ovpn_user_id}', '{ip}', '{file_path}', '{creation_date}', "
                       f"'{expiration_date}') "
                       f"RETURNING id, server_id, ovpn_user_id, ip, file_path, "
                       f"creation_date, expiration_date;")
        records = await session.execute(text(sql_request))
        return [tuple(record) for record in records][0]

    @staticmethod
    async def delete_certificate(session, certificate_id: int) -> typing.Tuple[
        int, int, int, str, str, datetime.datetime, datetime.datetime]:
        sql_request = (f"DELETE from public.certificates WHERE id = {certificate_id} "
                       f"RETURNING id, server_id, ovpn_user_id, ip, file_path, "
                       f"creation_date, expiration_date;")
        records = await session.execute(text(sql_request))
        return [tuple(record) for record in records][0]

