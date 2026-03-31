from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
import datetime as dt

# FOR INTEGRITY ERROR HANDLING
from sqlalchemy.exc import IntegrityError


# FOR FK ENFORCEMENT IN SQLlite
# from sqlalchemy import event
# from sqlalchemy.engine import Engine

# Database file definition
DB_ENGINE_URL = "sqlite:///./data/test_01.db"

engine = create_engine(DB_ENGINE_URL, echo=True)

## ENABLE FK ENFORCEMENT
# Needs to be placed after engine creation
# @event.listens_for(Engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA foreign_keys=ON")
#     cursor.close()

Base = declarative_base()

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



# START DB Engine
Base.metadata.create_all(engine)

# START Session
Session = sessionmaker(bind=engine)
session = Session()


# TEST INSERT
try:
    new_user = User (
        email = 'test@email.com',
        first_name='Charlie', 
        last_name='Test',
        status = 'test',
        sign_user_id = 'sample_user_id_01'
        )
    session.add(new_user)

    # new_user = User (
    #     email = 'test2@email.com',
    #     first_name='Charlie2', 
    #     last_name='Test2',
    #     status = 'test',
    #     sign_user_id = 'sample_user_id_2'
    #     )
    # session.add(new_user)

    # FLUSH to obtain the person id
    # session.flush()
    
    # new_thing = Thing(description='Mouse Pad', value=9.90, owner=new_person.id) # Owner ID inexistente
    # session.add(new_thing)

    session.commit()
    print ("OK Transaction")

except IntegrityError as e:
    # Reverts Person and Things update
    session.rollback()
    print (f"Error: Integrity: {e}")
except Exception as e:
    session.rollback()
    print (f"Error: Unexpected: {e}")

# TEST UPDATE

# try:
#     update_user = User (
#         email = 'test@email.com',
#         first_name='Charlie', 
#         last_name='Test',
#         status = 'test',
#         adobe_user_id = 'sample_user_id'
#         )
#     session.update(update_user)

#     # FLUSH to obtain the person id
#     # session.flush()
    
#     # new_thing = Thing(description='Mouse Pad', value=9.90, owner=new_person.id) # Owner ID inexistente
#     # session.add(new_thing)

#     session.commit()
#     print ("OK Transaction")

# except IntegrityError as e:
#     # Reverts Person and Things update
#     session.rollback()
#     print (f"Error: Integrity: {e}")
# except Exception as e:
#     session.rollback()
#     print (f"Error: Unexpected: {e}")




# SESSION CLOSE
session.close()


