from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Enum, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class RaceStatus(str, enum.Enum):
    INGESTED = "INGESTED"
    VERIFIED = "VERIFIED"
    PROCESSING = "PROCESSING"

class SCStatus(str, enum.Enum):
    GREEN = "GREEN"
    SC = "SC"
    VSC = "VSC"
    RED_FLAG = "RED_FLAG"
    YELLOW = "YELLOW"

class RaceModel(Base):
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    season = Column(Integer, nullable=False)
    round = Column(Integer, nullable=False)
    circuit_id = Column(String, nullable=False)
    status = Column(Enum(RaceStatus), default=RaceStatus.INGESTED)

    states = relationship("RaceStateModel", back_populates="race", cascade="all, delete-orphan")
    telemetry = relationship("TelemetryModel", back_populates="race", cascade="all, delete-orphan")

class RaceStateModel(Base):
    __tablename__ = "race_states"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id", ondelete="CASCADE"), nullable=False)
    tick = Column(Integer, nullable=False)
    lap = Column(Integer, nullable=False)
    sc_status = Column(Enum(SCStatus), default=SCStatus.GREEN)
    weather_data = Column(JSONB)

    race = relationship("RaceModel", back_populates="states")

class TelemetryModel(Base):
    __tablename__ = "telemetry"
    # For a TimescaleDB hypertable, 'time' is usually part of the primary key.
    # In SQLAlchemy, we can specify primary_key=True on multiple columns to allow this.

    time = Column(DateTime, primary_key=True, nullable=False)
    driver_id = Column(String, primary_key=True, nullable=False)
    race_id = Column(Integer, ForeignKey("races.id", ondelete="CASCADE"), nullable=False)
    lap = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    speed = Column(Float, nullable=False)
    tire_compound = Column(String, nullable=False)
    tire_wear = Column(Float, nullable=False)
    win_probability = Column(Float, nullable=True)

    race = relationship("RaceModel", back_populates="telemetry")
