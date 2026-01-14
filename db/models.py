from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.sql import func
from db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    snippet = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False, unique=True)
    source = Column(String(100), nullable=True)
    score = Column(Float, default=0.0)
    is_new = Column(Boolean, default=True)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    jobs_found = Column(Integer, default=0)
    new_jobs = Column(Integer, default=0)
    status = Column(String(50), default="running")
    error_message = Column(Text, nullable=True)


class DigestRun(Base):
    __tablename__ = "digest_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    jobs_sent = Column(Integer, default=0)
    recipient_email = Column(String(255), nullable=True)
    status = Column(String(50), default="running")
    error_message = Column(Text, nullable=True)
