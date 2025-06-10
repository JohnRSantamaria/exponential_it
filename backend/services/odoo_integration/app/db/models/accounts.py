from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Account(Base):
    __tablename__ = "accounts_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users_user.id"))
    name = Column(String(100), nullable=False)
    created = Column(DateTime)

    user = relationship("User", back_populates="accounts")
    account_services = relationship("AccountService", back_populates="account")
