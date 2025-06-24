from pydantic import BaseModel
from typing import List



class UserDataSchema(BaseModel):
    user_id: int
    email: str
    active_subscriptions: List[int]
    exp: int

    class Config:
        from_attributes = True  
