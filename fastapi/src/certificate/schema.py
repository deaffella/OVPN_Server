from pydantic import BaseModel, Field
from datetime import datetime
import typing


class Certificate(BaseModel):
    id: int = Field(..., example="1", description="Unique id for certificate.")
    server_id: int = Field(..., example="1", description="Unique id for server.")
    ovpn_user_id: int = Field(..., example="2", description="Unique id for ovpn user.")
    ip: str = Field(..., example="10", description="Internal ip for ovpn user. (value `10` set attr as `server_subnet`.10)")
    file_path: str = Field(...)
    creation_date: datetime = Field(..., example="2019-04-01T03:00:00+03:00", description="ISO 8601 format")
    expiration_date: datetime = Field(..., example="2019-04-01T03:00:00+03:00", description="ISO 8601 format")
    url: str = Field(...)


class AddCertificate(BaseModel):
    server_id: int = Field(..., example="1", description="Unique id for server.")
    ovpn_user_id: int = Field(..., example="2", description="Unique id for ovpn user.")
    client_ip_last_octet: str = Field(..., example="10", description="Internal ip for ovpn user. (value `10` set attr as `server_subnet`.10)")
    expiration_date: datetime = Field(..., example="2019-04-01T03:00:00+03:00", description="ISO 8601 format")


class DeleteCertificate(BaseModel):
    id: int = Field(..., example="1", description="Unique id for certificate.")


