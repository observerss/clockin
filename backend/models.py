from datetime import datetime
import enum
from colorama import Fore
from sqlalchemy import Float, inspect, alias, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Float,
    JSON,
    DateTime,
    Date,
    Enum,
)
from sqlalchemy.orm import relationship, deferred

from config import get_config

engine = create_engine(
    get_config()["database"]["url"], connect_args={"check_same_thread": False}
)
Session = sessionmaker(bind=engine)

Base = declarative_base()


class PlanType(enum.Enum):
    script = 1
    installation = 2


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, index=True)
    token = Column(String)
    avatar_url = Column(String)
    name = Column(String)
    balance = Column(Float)
    role = Column(String)
    plan = Column(String)
    referral_code = Column(String)
    referral_count = Column(Integer)

    cookie = Column(String)

    robots = relationship("Robot", back_populates="user")
    scripts = relationship("Script", back_populates="user")
    installations = relationship("Installation", back_populates="user")
    plans = relationship("Plan", back_populates="user")
    records = relationship("Record", back_populates="user")
    clocks = relationship("Clock", back_populates="user")


class Robot(Base):
    __tablename__ = "robots"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    deleted = Column(Boolean, index=True, default=False)

    online = Column(Boolean)
    version = Column(String)
    brand = Column(String)
    model = Column(String)
    app_version_code = Column(Integer)
    name = Column(String)

    user = relationship("User", back_populates="robots")
    plans = relationship("Plan", back_populates="robot")
    records = relationship("Record", back_populates="robot")


class Script(Base):
    __tablename__ = "scripts"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    deleted = Column(Boolean, index=True, default=False)

    name = Column(String, index=True)
    obfuscate = Column(Boolean)
    use_message = Column(Boolean)
    updated_at = Column(DateTime)
    listing_slug = Column(String)
    configuration = deferred(Column(JSON))
    files = deferred(Column(JSON))

    user = relationship("User", back_populates="scripts")
    plans = relationship("Plan", back_populates="script")


class Installation(Base):
    __tablename__ = "installations"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    deleted = Column(Boolean, index=True, default=False)

    configuration = Column(JSON)
    plan = Column(JSON)
    has_update = Column(Boolean)
    settings = Column(JSON)
    slug = Column(String)
    name = Column(String)
    version = Column(String)
    icon = Column(String)
    use_for_task = Column(Boolean)

    user = relationship("User", back_populates="installations")
    plans = relationship("Plan", back_populates="installation")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(PlanType))
    user_id = Column(String, ForeignKey("users.id"))
    robot_id = Column(String, ForeignKey("robots.id"))
    script_id = Column(String, ForeignKey("scripts.id"))
    installation_id = Column(String, ForeignKey("installations.id"))
    deleted = Column(Boolean, index=True, default=False)
    ranges = Column(
        JSON, default={"clockin_range": "8:00-11:00", "clockout_range": "19:00-24:00"}
    )

    user = relationship("User", back_populates="plans")
    robot = relationship("Robot", back_populates="plans")
    script = relationship("Script", back_populates="plans")
    installation = relationship("Installation", back_populates="plans")


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String, ForeignKey("users.id"))
    robot_id = Column(String, ForeignKey("robots.id"))
    script_id = Column(String)

    app_env = Column(String)
    timestamp = Column(DateTime)
    extra = Column(JSON)

    user = relationship("User", back_populates="records")
    robot = relationship("Robot", back_populates="records")


class Clock(Base):
    __tablename__ = "clocks"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String, ForeignKey("users.id"))

    date = Column(Date)
    clockin = Column(Boolean, default=False)
    clockout = Column(Boolean, default=False)

    user = relationship("User", back_populates="clocks")


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
