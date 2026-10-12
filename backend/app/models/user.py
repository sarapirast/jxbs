from sqlalchemy import Column, String, DateTime, func
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # uuid4 hex, assigned at creation
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
