from pydantic import BaseModel, Field
from datetime import datetime
import typing




class AddServer(BaseModel):
    name: str = Field(..., example="ServerName", description="Unique name for server.")
    external_ip: str = Field(..., example="241.16.33.72", description="White external server ip.")
    external_port: int = Field(..., example="1194", description="External ovpn port.")
    internal_ip: str = Field(..., example="192.168.42.1", description="Internal server ip.")
    internal_port: int = Field(..., example="1194", description="Internal ovpn port.")
    internal_subnet: str = Field(..., example="192.168.42.0/24", description="internal subnet for ovpn network.")
    creation_date: datetime = Field(..., example="2019-04-01T03:00:00+03:00", description="ISO 8601 format")
    monitor_port: int = Field(..., example="4401", description="Port for ovpn monitor.")


class DeleteServer(BaseModel):
    id: int = Field(..., example="1", description="Unique id for server.")


