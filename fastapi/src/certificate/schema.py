from pydantic import BaseModel, Field
from datetime import datetime
import typing




class AddCertificate(BaseModel):
    server_id: int = Field(..., example="1", description="Unique id for server.")
    ovpn_user_id: int = Field(..., example="2", description="Unique id for ovpn user.")
    ip: str = Field(..., example="192.168.42.10", description="Internal ip for ovpn user.")
    file_path: str = Field(..., example="certificate.ovpn", description="File path for user certificate.")
    creation_date: datetime = Field(..., example="2019-04-01T03:00:00+03:00", description="ISO 8601 format")
    expiration_date: datetime = Field(..., example="2019-04-01T03:00:00+03:00", description="ISO 8601 format")


class DeleteCertificate(BaseModel):
    id: int = Field(..., example="1", description="Unique id for certificate.")


