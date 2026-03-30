from database import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    adobe_user_id = Column(String, nullable=False, unique=True)


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    adobe_group_id = Column(String, nullable=False, unique=True)

