from database import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    adobe_id = Column(String, nullable=False, unique=True)

    #things = relationship('Thing', back_populates='person')