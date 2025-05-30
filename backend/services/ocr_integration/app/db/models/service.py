# app/db/models/service.py

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Boolean,
    DateTime,
    LargeBinary,
    String,
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class Service(Base):
    __tablename__ = "services_service"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True)
    name = Column(String(100))
    description = Column(String)


class UserService(Base):
    __tablename__ = "services_userservice"

    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    date_subscribed = Column(DateTime, default=datetime.utcnow)
    service_id = Column(Integer, ForeignKey("services_service.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    credentials = relationship("ServiceCredential", back_populates="user_service")


class ServiceCredential(Base):
    __tablename__ = "services_servicecredential"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String)
    value = Column(LargeBinary)
    is_secret = Column(Boolean, default=False)
    user_service_id = Column(Integer, ForeignKey("services_userservice.id"))

    user_service = relationship("UserService", back_populates="credentials")
