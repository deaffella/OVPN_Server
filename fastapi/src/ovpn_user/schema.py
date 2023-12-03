from pydantic import BaseModel, Field
from datetime import datetime
import typing




class AddOvpnUser(BaseModel):
    nickname: str = Field(..., example="UserNickname", description="Nickname for ovpn user.")
    registration_date: datetime = Field(..., example="2019-04-01T03:00:00+03:00", description="ISO 8601 format")
    first_name: str = Field(..., example="FirstName", description="First name for ovpn user.")
    last_name: str = Field(..., example="LastName", description="Last name for ovpn user.")
    telegram_id: int = Field(..., example="123456789", description="User telegram id.")


class DeleteOvpnUser(BaseModel):
    id: int = Field(..., example="1", description="Unique id for ovpn user.")


