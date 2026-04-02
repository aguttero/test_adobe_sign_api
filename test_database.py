
# LOGGER CONFIG
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from test_models import User, Base

# from sqlalchemy import Column, Integer, String, Date
# from sqlalchemy.ext.declarative import declarative_base
# import datetime as dt

# FOR INTEGRITY ERROR HANDLING
# from sqlalchemy.exc import IntegrityError


# FOR FK ENFORCEMENT IN SQLlite
# from sqlalchemy import event
# from sqlalchemy.engine import Engine

# Database file definition
DB_ENGINE_URL = "sqlite:///./data/test_02.db"

engine = create_engine(DB_ENGINE_URL, echo=True)

## ENABLE FK ENFORCEMENT
# Needs to be placed after engine creation
# @event.listens_for(Engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA foreign_keys=ON")
#     cursor.close()

# START DB Engine
Base.metadata.create_all(engine)


# START Session class
Session = sessionmaker(bind=engine)
# session = Session()

# TEST SAFE INSERT
# V1

# TODO db.py
# with error management and logging
# Sample Gemini Code

test_user_list = []

def update_users(user_list):
    if not user_list:
        logger.warning("no user list")
        return
    
    session = Session()
    try:
        for dict_item in user_list:
            new_item = User(
                email= dict_item.get('email'),
                sign_user_id = dict_item.get('id')
            )
            session.merge(new_item)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"{e}")
        raise e
    finally:
        session.close()


# TEST INSERT
def try_insert(dict_item):
    session = Session()
    try:
        new_user = User (
            email = dict_item.get('email'),
            first_name = dict_item.get('first_name'),
            last_name = dict_item.get('last_name'),
            status = dict_item.get('status'),
            sign_user_id = dict_item.get('sign_user_id')
            )
        session.add(new_user)

        # Manually insert 1 user:
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
        logger.info("Ok insert user")

    except IntegrityError as e:
        # Reverts Person and Things update
        session.rollback()
        print (f"Error: Integrity: {e}")
        logger.error(f"{e}")
        # raise IntegrityError (f"{e}", params="params", orig="orig")
    except Exception as e:
        session.rollback()
        logger.error(f"{e}")
        print (f"Error: Unexpected: {e}")
        # raise Exception (f"{e}", params="params", orig="orig")
    finally:
        session.close()
        logger.info("FINALLY!!")

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



