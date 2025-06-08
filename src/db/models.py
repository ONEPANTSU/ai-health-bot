from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    UUID,
    ForeignKey,
    JSON,
    ARRAY,
    BigInteger,
)
import uuid

Base = declarative_base()


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    full_name = Column(String)
    timezone = Column(String, default="UTC")  # Новое поле
    registered_at = Column(DateTime, server_default="now()")
    is_active = Column(Boolean, default=True)
    testing_start_date = Column(DateTime)


class PatientHistory(Base):
    __tablename__ = "patient_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID, ForeignKey("patients.id"))
    answers = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default="now()")
    gpt_response = Column(String)
    s3_files = Column(ARRAY(String))
    summary = Column(String)
