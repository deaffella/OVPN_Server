
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.exceptions import HTTPException


import os
from bson import ObjectId
import json
import subprocess
import datetime

from src.database.database import Database_Sync as Database

from src.server.schema import AddServer, DeleteServer
from src.ovpn_user.schema import AddOvpnUser, DeleteOvpnUser
from src.certificate.schema import AddCertificate, DeleteCertificate



from src.settings import PG


db = Database(host=PG['host'], port=PG['port'], user=PG['user'], password=PG['password'], db_name=PG['db'])


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




@app.get("/servers/get_list", tags=["servers"])
async def get_servers_list():
    servers = db.get_servers_list()
    return servers

@app.post("/servers/add", tags=["servers"])
async def add_server(server: AddServer):
    try:
        data = json.loads(server.json())
        servers = db.add_server(name=data['name'],
                                external_ip=data['external_ip'],
                                external_port=data['external_port'],
                                internal_ip=data['internal_ip'],
                                internal_port=data['internal_port'],
                                internal_subnet=data['internal_subnet'],
                                creation_date=data['creation_date'],
                                monitor_port=data['monitor_port'])
        return servers
    except Exception as e:
        raise HTTPException(409, detail=str(e))

@app.delete("/servers/delete", tags=["servers"])
async def delete_server(server: DeleteServer):
    try:
        data = json.loads(server.json())
        servers = db.delete_server(server_id=data['id'])
        return servers
    except Exception as e:
        raise HTTPException(409, detail=str(e))




@app.get("/ovpn_users/get_list", tags=["ovpn_users"])
async def get_ovpn_users_list():
    ovpn_users = db.get_ovpn_users_list()
    return ovpn_users

@app.post("/ovpn_users/add", tags=["ovpn_users"])
async def add_ovpn_user(server: AddOvpnUser):
    try:
        data = json.loads(server.json())
        ovpn_users = db.add_ovpn_user(nickname=data['nickname'],
                                      registration_date=data['registration_date'],
                                      first_name=data['first_name'],
                                      last_name=data['last_name'],
                                      telegram_id=data['telegram_id'])
        return ovpn_users
    except Exception as e:
        raise HTTPException(409, detail=str(e))

@app.delete("/ovpn_users/delete", tags=["ovpn_users"])
async def delete_ovpn_user(server: DeleteOvpnUser):
    try:
        data = json.loads(server.json())
        ovpn_users = db.delete_ovpn_user(ovpn_user_id=data['id'])
        return ovpn_users
    except Exception as e:
        raise HTTPException(409, detail=str(e))




@app.get("/certificates/get_list", tags=["certificates"])
async def get_certificates_list():
    certificates = db.get_certificates_list()
    return certificates

@app.post("/certificates/add", tags=["certificates"])
async def add_certificate(server: AddCertificate):
    try:
        data = json.loads(server.json())
        certificates = db.add_certificate(server_id=data['server_id'],
                                          ovpn_user_id=data['ovpn_user_id'],
                                          ip=data['ip'],
                                          file_path=data['file_path'],
                                          creation_date=data['creation_date'],
                                          expiration_date=data['expiration_date'])
        return certificates
    except Exception as e:
        raise HTTPException(409, detail=str(e))

@app.delete("/certificates/delete", tags=["certificates"])
async def delete_ovpn_user(server: DeleteCertificate):
    try:
        data = json.loads(server.json())
        certificates = db.delete_certificate(certificate_id=data['id'])
        return certificates
    except Exception as e:
        raise HTTPException(409, detail=str(e))



