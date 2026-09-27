from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    role = Column(String, nullable=False, default="student")
    hash_password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    # set when a "forgot password" flow issues one; cleared after use.
    # NOTE: no endpoint issues this yet — /change-password has nothing to
    # check against until a /forgot-password (or similar) endpoint exists.
    recovery_code = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
