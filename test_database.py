
## LOGGER CONFIG
import logging
logger = logging.getLogger(__name__)

from typing import Type, List
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
logger.debug("from test_models import Base START")
from test_models import Base, User
logger.debug("from test_models import Base END")


# FOR INTEGRITY ERROR HANDLING
# from sqlalchemy.exc import IntegrityError

# FOR FK ENFORCEMENT IN SQLlite via connection event monitoring
# from sqlalchemy import event
# from sqlalchemy.engine import Engine

## CONFIG



# Database file definition
logger.debug("DB_ENGINE_URL var def START")
DB_ENGINE_URL = "sqlite:///./data/test_01.db"
logger.debug("DB_ENGINE_URL var def END")

logger.debug("create_engine START")
engine = create_engine(DB_ENGINE_URL, echo=True)
logger.debug("create_engine END")

## ENABLE FK ENFORCEMENT
# Needs to be placed after engine creation
# @event.listens_for(Engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA foreign_keys=ON")
#     cursor.close()

# START DB Engine
logger.debug("base.metadata.create_all(engine) START")
Base.metadata.create_all(engine)
logger.debug("base.metadata.create_all(engine) END")

# START Session class
logger.debug("Session class start and bind START")
Session = sessionmaker(bind=engine)
logger.debug("Session class start and bind END")
# session = Session()

# TEST SAFE INSERT
# V1

# TODO db.py
# with error management and logging
# Sample Gemini Code

def select_user_by_email(searched_email:str) -> User:
    """ Selects single user by email key with session.execute. Returns User instance. ORM 2"""
    with Session() as session:
        result = session.execute(select(User).filter_by(email=searched_email)).scalar_one()
        return result

def update_user_status_by_email(searched_email:str, new_status:str):
    """ Updates status field of single user by email key. ORM 2"""
    with Session() as session:
        stmt = select(User).filter_by(email=searched_email)
        user = session.execute(stmt).scalar_one_or_none()

        if user:
            user.status = new_status
            session.commit()
            logger.debug("update ok")
        else:
            logger.debug(f"usuario {searched_email} no encontrado")

def update_user_status_by_email_2(searched_email:str, new_status:str):
    """ Updates status field of single user by email key. Uses session.begin(). ORM 2"""
    with Session() as session:
        with session.begin(): #Auto commit / rollback inside this with
            stmt = select(User).filter_by(email=searched_email)
            user = session.execute(stmt).scalar_one_or_none()

            if user:
                user.status = new_status
                logger.debug("update ok")
            else:
                logger.debug(f"usuario {searched_email} no encontrado")

def update_users(user_list: list[dict]):
    """Upserts User table using email as the natural key.
    Uses session.merge
    - INSERTs new users (email not yet in DB).
    - UPDATEs existing users (matched by email), leaving `id` untouched.
    """
    # from test_models import User
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
        # raise e
    finally:
        session.close()
        logger.debug("update_users -> session.close")

def test_convert_txt_to_list(filename:str) -> list:
    """Converts file.txt user list to python list"""
    import ast

    with open (filename, "r") as file:
        file_content = file.read()

    user_list = ast.literal_eval(file_content)
    print ("- - - - ")
    print ("DEBUG PRINT - Function: Convert file.txt to user_list")
    print ("len user_list:", len(user_list))
    print (f"{user_list[0]}\n{user_list[1]}\n{user_list[len(user_list)-1]}")
    print ("- - - - ")
    
    return user_list

# TEST OK 20260407
def test_transform_user_list_keys(input_list: list[dict]) -> list[dict]:
    """ Transforms user_list dict keys from Adobe Sign API format to app Database format """
    transformed_list = [{
        'email': item['email'],
        'adbe_sign_id': item ['id']
    }
    for item in input_list]
    
    return transformed_list

# OK TEST 20260407
def test_bulk_insert_list(table_class: Type[Base], input_list: list[dict]):
# def test_bulk_insert_list(table_class: Type[Base], input_list: List[dict]):
    """bulk insert list of users ORM 2.0."""
 
    from sqlalchemy import insert
    with Session() as session:
        try:
            session.execute(insert(table_class), input_list)
            session.commit()
            logger.debug("ok bulk insert list")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"func: bulk_insert_list: SQLA error: {e}")
            # raise DatabaseError()
        except Exception as e:
            session.rollback()
            logger.error(f"func: bulk_insert_list: Exception error: {e}")
            # raise DatabaseError()
        finally:
            if session.is_active:
                logger.debug(f"session 'is active' status in finally: {session.is_active}")
    logger.debug("pasa por aca?")
    logger.debug(f"session 'is active' status at end: {session.is_active}")

# OK - TEST INSERT - 20260407
def insert_users_session_add(dict_item: dict):
    """Inserts a single dict user into User table with session add"""
    #from test_models import User
    session = Session()
    try:
        new_user = User (
            email = dict_item.get('email'),
            first_name = dict_item.get('first_name'),
            last_name = dict_item.get('last_name'),
            status = dict_item.get('status'),
            adbe_sign_id = dict_item.get('adbe_sign_id')
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
        logger.debug(f"session 'is_active' status in sesssion add: {session.is_active}")
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



