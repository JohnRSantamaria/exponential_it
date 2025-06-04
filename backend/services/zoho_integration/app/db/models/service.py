# app/db/models/service.py

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Boolean,
    DateTime,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class Service(Base):
    __tablename__ = "services_service"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True)
    name = Column(String(100))
    description = Column(Text)

    account_services = relationship("AccountService", back_populates="service")


class AccountService(Base):
    __tablename__ = "services_accountservice"
    __table_args__ = (
        UniqueConstraint("account_id", "service_id", name="_account_service_uc"),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts_account.id"))
    service_id = Column(Integer, ForeignKey("services_service.id"))

    account = relationship("Account", back_populates="account_services")
    service = relationship("Service", back_populates="account_services")
    credentials = relationship("ServiceCredential", back_populates="account_service")


class ServiceCredential(Base):
    __tablename__ = "services_servicecredential"

    id = Column(Integer, primary_key=True, index=True)
    account_service_id = Column(Integer, ForeignKey("services_accountservice.id"))
    key = Column(String(100))
    value = Column(LargeBinary)
    is_secret = Column(Boolean, default=False)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow)

    account_service = relationship("AccountService", back_populates="credentials")
