import time
from typing import List, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.exceptions import HTTPException
import starlette.status as status


import os
import json
import datetime
from traceback import format_exc
from uuid import uuid4

from src.utils.docker_client import OVPN_Docker_Client as DockerClient
from src.database.database import Database_Sync as Database

from src.server.schema import AddServer, DeleteServer
from src.ovpn_user.schema import AddOvpnUser, DeleteOvpnUser
from src.certificate.schema import AddCertificate, DeleteCertificate, Certificate


from src.settings import PG


db = Database(host=PG['host'], port=PG['port'], user=PG['user'], password=PG['password'], db_name=PG['db'])
docker = DockerClient()


app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event('startup')
async def startup():
    db.connect()
    db.create_tables(verbose=True)


@app.get("/")
async def main():
    # Redirect to /docs (relative URL)
    return RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)



@app.get("/servers/run", tags=["servers"])
async def run_server(server_id: int):
    selected_server = db.get_server_by_id(server_id=server_id)
    if type(selected_server) == type(None):
        raise HTTPException(403, detail=f'Server does not exist:\n{server_id}')
    server_id, server_name = selected_server[:2]
    server = docker.run_ovpn_server_container(name=server_name)
    return server

@app.get("/servers/status", tags=["servers"])
async def status_server(server_id: int):
    selected_server = db.get_server_by_id(server_id=server_id)
    if type(selected_server) == type(None):
        raise HTTPException(403, detail=f'Server does not exist:\n{server_id}')
    server_id, server_name = selected_server[:2]
    server = docker.status_ovpn_server_container(name=server_name)
    return server

@app.get("/servers/get_list", tags=["servers"])
async def get_servers_list():
    servers = db.get_servers_list()
    return servers

@app.post("/servers/add", tags=["servers"])
async def add_server(server: AddServer):
    data = json.loads(server.json())
    server_exist = db.get_server_by_name(name=data['name'])
    if type(server_exist) != type(None):
        raise HTTPException(403, detail=f'Server already exist:\n{data}')

    subnet, mask = data['internal_subnet'].split('/')[:2]
    docker.create_ovpn_server_container(name=data['name'],
                                        internal_port=data['internal_port'],
                                        external_port=data['external_port'],
                                        ext_ip=data['external_ip'],
                                        subnet=subnet,
                                        mask=mask)
    # docker.configure_ovpn_server_container(name=data['name'],
    #                                        ext_ip=data['external_ip'],
    #                                        subnet=subnet,
    #                                        mask=mask)
    servers = db.add_server(name=data['name'],
                            external_ip=data['external_ip'],
                            external_port=data['external_port'],
                            internal_ip=data['internal_ip'],
                            internal_port=data['internal_port'],
                            internal_subnet=data['internal_subnet'],
                            creation_date=data['creation_date'],
                            monitor_port=data['monitor_port'])
    return servers

@app.delete("/servers/delete", tags=["servers"])
async def delete_server(server: DeleteServer):
    data = json.loads(server.json())
    selected_server = db.get_server_by_id(server_id=data['id'])
    if type(selected_server) == type(None):
        raise HTTPException(403, detail=f'Server does not exist:\n{data}')
    server_id, server_name = selected_server[:2]
    docker.remove_ovpn_server_container(name=server_name)
    servers = db.delete_server(server_id=data['id'])
    return servers




@app.get("/ovpn_users/get_list", tags=["ovpn_users"])
async def get_ovpn_users_list():
    ovpn_users = db.get_ovpn_users_list()
    return ovpn_users

@app.get("/ovpn_users/get_by_id/{user_id}", tags=["ovpn_users"])
async def get_ovpn_user_by_id(user_id: int):
    ovpn_users = db.get_ovpn_user_by_id(ovpn_user_id=user_id)
    return ovpn_users

@app.get("/ovpn_users/get_by_user_name/{user_name}", tags=["ovpn_users"])
async def get_ovpn_user_by_user_name(user_name: str):
    ovpn_users = db.get_ovpn_user_by_name(name=user_name)
    return ovpn_users

@app.post("/ovpn_users/add", tags=["ovpn_users"])
async def add_ovpn_user(server: AddOvpnUser):
    data = json.loads(server.json())
    ovpn_user_exist = db.get_ovpn_user_by_name(name=data['nickname'])
    if type(ovpn_user_exist) != type(None):
        raise HTTPException(403, detail=f'OVPN user already exist:\n{data}')

    ovpn_users = db.add_ovpn_user(nickname=data['nickname'],
                                  registration_date=data['registration_date'],
                                  first_name=data['first_name'],
                                  last_name=data['last_name'],
                                  telegram_id=data['telegram_id'])
    return ovpn_users

@app.delete("/ovpn_users/delete", tags=["ovpn_users"])
async def delete_ovpn_user(server: DeleteOvpnUser):
    data = json.loads(server.json())
    ovpn_user_exist = db.get_ovpn_user_by_id(ovpn_user_id=data['id'])
    if type(ovpn_user_exist) == type(None):
        raise HTTPException(403, detail=f'OVPN user does not exist:\n{data}')
    exist_certificates_for_user = db.get_certificates_list_for_user(ovpn_user_id=data['id'])
    if type(exist_certificates_for_user) == list:
        for exist_certificate in exist_certificates_for_user:
            certificate_id, server_id, ovpn_user_id, _, file_name = exist_certificate[:5]
            _, container_name = db.get_server_by_id(server_id=server_id)[:2]
            docker.ovpn_certificate_remove(container_name=container_name, cert_name=file_name)
            db.delete_certificate(certificate_id=certificate_id)
    ovpn_users = db.delete_ovpn_user(ovpn_user_id=data['id'])
    return ovpn_users




@app.get("/certificates/get_list", tags=["certificates"])
async def get_certificates_list():
    certificates = db.get_certificates_list()
    return certificates

@app.get("/certificates/get_by_id/{certificate_id}", tags=["certificates"])
async def get_certificate_by_id(certificate_id: int) -> str:
    ovpn_certificate = db.get_certificate_by_id(certificate_id=certificate_id)
    if type(ovpn_certificate) == type(None):
        raise HTTPException(403, detail=f'OVPN certificate doest not exist:\n{certificate_id}')
    certificate_id, server_id, ovpn_user_id, ip, file_name = ovpn_certificate[:5]
    _, container_name = db.get_server_by_id(server_id=server_id)[:2]
    certificate_content = docker.ovpn_certificate_content_get(container_name=container_name, file_name=file_name)
    tmp_file = f'/tmp/{uuid4()}.cert'
    with open(tmp_file, 'w') as file:
        file.write(certificate_content)
    return FileResponse(tmp_file,
                        filename=file_name,
                        media_type="application/octet-stream",
                        headers={"Content-Disposition": f"attachment; filename={file_name}"})


@app.get("/certificates/get_by_user_name/{user_name}", tags=["certificates"])
async def get_certificates_by_user_name(user_name: str) -> list[Any]:
    ovpn_user_exist = db.get_ovpn_user_by_name(name=user_name)
    if type(ovpn_user_exist) == type(None):
        raise HTTPException(403, detail=f'OVPN user does not exist:\n{user_name}')
    ovpn_user_id = ovpn_user_exist[0]
    exist_certificates_for_user = db.get_certificates_list_for_user(ovpn_user_id=ovpn_user_id)
    if type(ovpn_user_exist) == type(None):
        return []
    return [Certificate(id=certificate_id,
                        server_id=server_id,
                        ovpn_user_id=ovpn_user_id,
                        ip=ip,
                        file_path=file_path,
                        creation_date=creation_date,
                        expiration_date=expiration_date,
                        url=f'/certificates/get_by_id/{certificate_id}')
            for (certificate_id, server_id, ovpn_user_id, ip, file_path, creation_date, expiration_date)
            in exist_certificates_for_user]


@app.post("/certificates/add", tags=["certificates"])
async def add_certificate(server: AddCertificate):
    data = json.loads(server.json())
    server_exist = db.get_server_by_id(server_id=data['server_id'])
    if not isinstance(server_exist, tuple):
        raise HTTPException(403, detail=f'OVPN server does not exist:\n{data}')
    ovpn_user_exist = db.get_ovpn_user_by_id(ovpn_user_id=data['ovpn_user_id'])
    if not isinstance(ovpn_user_exist, tuple):
        raise HTTPException(403, detail=f'OVPN user does not exist:\n{data}')
    server_id, container_name, _, _, internal_server_ip = server_exist[:5]
    client_ip = f"{'.'.join(internal_server_ip.split('.')[:-1])}.{data['client_ip_last_octet']}"

    ovpn_certificates = db.get_certificate_by_server_id_and_user_id_and_ip(server_id=data['server_id'],
                                                                           ovpn_user_id=data['ovpn_user_id'],
                                                                           ip=client_ip)
    if type(ovpn_certificates) != type(None):
        raise HTTPException(403, detail=f'OVPN certificate already exist:\n{data}')

    certificate_file_name = f"server-{data['server_id']}_client-{data['ovpn_user_id']}_{client_ip}.ovpn"
    docker.ovpn_certificate_create(container_name=container_name,
                                   cert_file_name=certificate_file_name,
                                   client_ip=client_ip)
    created_certificate = db.add_certificate(server_id=data['server_id'],
                                             ovpn_user_id=data['ovpn_user_id'],
                                             ip=client_ip,
                                             file_name=certificate_file_name,
                                             creation_date=datetime.datetime.now(),
                                             expiration_date=datetime.datetime.now()) # TODO: ADD EXP DATE
    return created_certificate

@app.delete("/certificates/delete", tags=["certificates"])
async def delete_certificate(certificate: DeleteCertificate):
    data = json.loads(certificate.json())
    ovpn_certificate = db.get_certificate_by_id(certificate_id=data['id'])
    if type(ovpn_certificate) == type(None):
        raise HTTPException(403, detail=f'OVPN certificate already exist:\n{data}')
    certificate_id, server_id, ovpn_user_id, ip, file_path = ovpn_certificate[:5]
    _, container_name = db.get_server_by_id(server_id=server_id)[:2]
    docker.ovpn_certificate_remove(container_name=container_name, cert_name=file_path)
    certificates = db.delete_certificate(certificate_id=certificate_id)
    return certificates



