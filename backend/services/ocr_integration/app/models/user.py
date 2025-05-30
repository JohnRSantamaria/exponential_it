# app/models/user.py
from pydantic import BaseModel


class UserBase(BaseModel):
    email: str
    name: str
    last_name: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_staff: bool

    class Config:
        from_attributes = True
