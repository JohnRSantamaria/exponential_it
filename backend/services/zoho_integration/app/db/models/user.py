# app/db/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.base import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String(150))
    last_name = Column(String(150))
    is_active = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    hashed_password = Column(String)
    date_joined = Column(DateTime, default=datetime.utcnow)
