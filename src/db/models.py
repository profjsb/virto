from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from . import Base

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    amount_usd = Column(Float, nullable=False)
    justification = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="pending")  # pending|approved|rejected|auto_approved
    threshold = Column(Float, nullable=False, default=50.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    decided_at = Column(DateTime(timezone=True), nullable=True)

class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(64), nullable=False)   # minutes|plan|run|other
    name = Column(String(255), nullable=False)
    path = Column(Text, nullable=False)         # file path where persisted (md/json/etc)
    storage = Column(String(16), nullable=False, server_default='local')
    s3_bucket = Column(String(255), nullable=True)
    s3_key = Column(String(512), nullable=True)
    content_type = Column(String(128), nullable=True)
    meta = Column(Text, nullable=True)          # json string for extra metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, index=True)
    run_type = Column(String(64), nullable=False)  # autogen|flow|job
    status = Column(String(32), nullable=False, default="created")
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UsageEvent(Base):
    __tablename__ = "usage_events"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=True)
    actor = Column(String(128), nullable=True)           # persona/agent name
    model = Column(String(128), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


from sqlalchemy import ForeignKey, Table
from sqlalchemy.orm import relationship

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)

class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))

class RunLog(Base):
    __tablename__ = "run_logs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    at = Column(DateTime(timezone=True), server_default=func.now())
    level = Column(String(16), nullable=False, default="info")
    message = Column(Text, nullable=False)
