# LOGGER CONFIG
import logging
logger = logging.getLogger(__name__)

import datetime as dt
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String,Date

logger.debug("class Base creation START")
class Base (DeclarativeBase):
    pass
logger.debug("class Base creation END")

logger.debug("class User creation START")
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    job_area = Column(String)
    job_title = Column(String)
    status = Column(String)
    sign_user_id = Column(String, nullable=False, unique=True, index=True)
    last_sync = Column(Date, default=dt.datetime.today(), onupdate=dt.datetime.today())
logger.debug("class User creation END")

logger.debug("End test Models.py")

# class Group(Base):
#     __tablename__ = 'groups'
#     id = Column(Integer, primary_key=True)
#     email = Column(String, nullable=False, unique=True)
#     adobe_group_id = Column(String, nullable=False, unique=True)

