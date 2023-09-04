import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import subprocess
from datetime import datetime


DB_NAME = "OVPN"
COLLECTION_NAME = "users"


# Подключение к MongoDB с помощью Motor
client = AsyncIOMotorClient(f"mongodb://"
                            f"{os.getenv('MONGODB_INITDB_ROOT_USERNAME')}:{os.getenv('MONGODB_INITDB_ROOT_PASSWORD')}"
                            f"@"
                            f"{os.getenv('ME_CONFIG_MONGODB_SERVER')}:{27017}")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


app = FastAPI()


@app.post("/add_user/", tags=["management"])
async def add_user(name: str, ip: str):
    certificate_path = f'/etc/openvpn/ccd/{name}.ovpn'

    existing_name = await collection.find_one({"name": name})
    if existing_name:
        raise HTTPException(status_code=400, detail=f"User `{name}` already exists")
    existing_ip = await collection.find_one({"ip": ip})
    if existing_ip:
        raise HTTPException(status_code=400, detail=f"IP `{ip}` already linked to user: `{existing_ip['name']}`")
    try:
        # create cert
        easyrsa_result = subprocess.run(
            [f"easyrsa --passin=file:passfile.secret --passout=file:passfile.secret build-client-full {name} nopass"],
            capture_output=True, text=True, check=True, shell=True)

        # copy cert to dir
        getclient_result = subprocess.run(
            [f'printf "# ip:\t{ip}\n\n" > /etc/openvpn/ccd/{name}.ovpn'
             f' && '
             f'ovpn_getclient {name} >> /etc/openvpn/ccd/{name}.ovpn'],
            capture_output=True, text=True, check=True, shell=True)

        # create static client ip
        static_ip_result = subprocess.run(
            [f'echo "ifconfig-push {ip} 255.255.255.0" > /etc/openvpn/ccd/{name}'],
            capture_output=True, text=True, check=True, shell=True)

        # Вставка данных в коллекцию
        result = await collection.insert_one({"name": name,
                                              "ip": ip,
                                              "certificate": certificate_path,
                                              "created_at": datetime.now()})
        return FileResponse(certificate_path,
                            filename=f"{name}.ovpn",
                            media_type="application/octet-stream",
                            headers={"Content-Disposition": f"attachment; filename={name}.ovpn"})
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={'error': str(e)})

@app.delete("/delete_user/", tags=["management"])
async def delete_user(name: str):
    existing_name = await collection.find_one({"name": name})
    if not existing_name:
        raise HTTPException(status_code=400, detail=f"User `{name}` not found")
    try:
        # revoke_client_certificate
        easyrsa_result = subprocess.run(
            [f'echo "yes" | easyrsa --passin=file:passfile.secret --passout=file:passfile.secret revoke {name}'],
            capture_output=True, text=True, check=True, shell=True)

        # gen-crl
        gen_crl_result = subprocess.run(
            [f'easyrsa --passin=file:passfile.secret --passout=file:passfile.secret gen-crl'],
            capture_output=True, text=True, check=True, shell=True)

        # cp and chmod
        cp_chmod_result = subprocess.run(
            [f'cp -f "$EASYRSA_PKI/crl.pem" "$OPENVPN/crl.pem" && chmod 644 "$OPENVPN/crl.pem"'],
            capture_output=True, text=True, check=True, shell=True)

        # rm from ccd
        cp_chmod_result = subprocess.run(
            [f'rm /etc/openvpn/ccd/{name} && rm /etc/openvpn/ccd/{name}.ovpn'],
            capture_output=True, text=True, check=True, shell=True)

        result = await collection.delete_one({"name": name})
        return {"message": f"User `{name}` deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail={'error': f"Cant delete user `{name}`",
                                                     'details': str(e)})

@app.get("/get_users/", tags=["show"])
async def get_users():
    users = []
    async for user in collection.find():
        user["_id"] = str(user["_id"])  # Преобразование ObjectId в строку
        users.append(user)
    return users

@app.get("/get_user_info/", tags=["show"])
async def get_user_info(name: str):
    user = await collection.find_one({"name": name})
    if user:
        user["_id"] = str(user["_id"])  # Преобразование ObjectId в строку
        return user
    else:
        raise HTTPException(status_code=404, detail=f"User `{name}` not found")

@app.get("/get_user_certificate/", tags=["download"])
async def get_user_certificate(name: str):
    user = await collection.find_one({"name": name})
    if user:
        certificate_path = user.get("certificate")
        if certificate_path and os.path.exists(certificate_path):
            return FileResponse(certificate_path,
                                filename=f"{name}.ovpn",
                                media_type="application/octet-stream",
                                headers={"Content-Disposition": f"attachment; filename={name}.ovpn"})
        else:
            raise HTTPException(status_code=404, detail=f"Certificate not found for user `{name}`")
    else:
        raise HTTPException(status_code=404, detail=f"User `{name}` not found")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
