from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# FOR FK ENFORCEMENT IN SQLlite
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Database file definition
DB_ENGINE_URL = "sqlite:///./data/adbe_sign_01.db"

engine = create_engine(DB_ENGINE_URL, echo=True)

# ENABLE FK ENFORCEMENT
# Needs to be placed after engine creation
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

Base = declarative_base()



