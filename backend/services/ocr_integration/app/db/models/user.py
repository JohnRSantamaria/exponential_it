# app/db/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users_user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    is_active = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=False)
    date_joined = Column(DateTime, default=datetime.utcnow)
    total_invoices_scanned = Column(Integer, default=0)

    accounts = relationship("Account", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User {self.email}>"
