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
DB_ENGINE_URL = "sqlite:///tests/data/test_01.db"
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


def check_db_last_closed_status() -> bool:
    """Check and update the database health status file.
    
    Reads the current DB health status from file and updates it.
    Returns True if DB was in clean state, False otherwise.
    """
    with open ("tests/data/db_health.txt","r+") as file:
        db_health_data = file.read()
        logger.debug(f"DB Health file value: {db_health_data}")
        file.seek(0)
        file.write("db_closed_status = 'Test - pending implementation'")
        file.truncate()
        if db_health_data == False:
            logger.warning(f"DB_SHUTDOWN_ERROR: The database did not reach a clean state during the last execution")
            return False
        else:
            return True


def select_user_by_email(searched_email: str) -> User:
    """Selects single user by email key. Returns User instance."""
    with Session() as session:
        result = session.execute(select(User).filter_by(email=searched_email)).scalar_one()
        return result


def update_user_status_by_email(searched_email: str, new_status: str) -> None:
    """Updates status field of single user by email key."""
    with Session() as session:
        stmt = select(User).filter_by(email=searched_email)
        user = session.execute(stmt).scalar_one_or_none()

        if user:
            user.status = new_status
            session.commit()
            logger.debug("update ok")
        else:
            logger.debug(f"usuario {searched_email} no encontrado")


def update_user_status_by_email_2(searched_email: str, new_status: str) -> None:
    """Updates status field using session.begin() for auto-commit/rollback."""
    with Session() as session:
        with session.begin():
            stmt = select(User).filter_by(email=searched_email)
            user = session.execute(stmt).scalar_one_or_none()

            if user:
                user.status = new_status
                logger.debug("update ok")
            else:
                logger.debug(f"usuario {searched_email} no encontrado")


def update_users(user_list: list[dict]) -> None:
    """Upserts User table using email as the natural key.
    
    Uses session.merge to INSERT new users (email not yet in DB)
    or UPDATE existing users (matched by email).
    
    Args:
        user_list: List of dicts with 'email' and 'adbe_sign_id' keys.
    """
    if not user_list:
        logger.warning("no user list")
        return
    
    with Session() as session:
        try:
            for dict_item in user_list:
                new_item = User(
                    email=dict_item.get('email'),
                    adbe_sign_id=dict_item.get('adbe_sign_id')
                )
                session.merge(new_item)
            session.commit()
            logger.info(f"Successfully upserted {len(user_list)} users")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to upsert users: {e}")
            raise


def test_convert_txt_to_list(filename: str) -> list:
    """Converts file.txt user list to python list.
    
    Args:
        filename: Path to the text file containing user list.
        
    Returns:
        List of user dictionaries parsed from file.
    """
    import ast

    with open(filename, "r") as file:
        file_content = file.read()
        logger.debug(f"OK Read: {filename} - {len(file_content)} chars")

    user_list = ast.literal_eval(file_content)
    logger.debug(f"OK Assign to list {len(user_list)} items")
    logger.debug(f"- - - - DEBUG: Function: Convert file.txt to user_list")
    logger.debug(f"len user_list: {len(user_list)}")
    logger.debug(f"- - - - ")
    return user_list


def test_transform_user_list_keys(input_list: list[dict]) -> list[dict]:
    """Transforms user_list dict keys from Adobe Sign API format to app Database format.
    
    Strips and lowercases email addresses. Converts 'id' key to 'adbe_sign_id'.
    
    Args:
        input_list: List of dicts from Adobe Sign API with 'email' and 'id' keys.
        
    Returns:
        List of dicts with 'email' (normalized) and 'adbe_sign_id' keys.
    """
    transformed_list = [
        {
            'email': item['email'].strip().lower(),
            'adbe_sign_id': item['id']
        }
        for item in input_list
    ]
    logger.debug(f"OK Transformed {len(transformed_list)} records")
    return transformed_list


def bulk_insert_list(table_name: Type[Base], input_list: list[dict]) -> None:
    """Bulk insert input_list into table for initial table load.
    
    Args:
        table_name: The SQLAlchemy model class to insert into.
        input_list: List of dictionaries representing rows to insert.
    """
    from sqlalchemy import insert
    with Session() as session:
        try:
            session.execute(insert(table_name), input_list)
            session.commit()
            logger.info(f"OK insert {len(input_list)} records into {table_name.__name__}")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"SQLA error during bulk insert: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error during bulk insert: {e}")
            raise


def insert_users_session_add(dict_item: dict) -> None:
    """Inserts a single dict user into User table with session add.
    
    Args:
        dict_item: Dictionary containing user fields.
    """
    with Session() as session:
        try:
            new_user = User(
                email=dict_item.get('email'),
                first_name=dict_item.get('first_name'),
                last_name=dict_item.get('last_name'),
                status=dict_item.get('status'),
                adbe_sign_id=dict_item.get('adbe_sign_id')
            )
            session.add(new_user)
            session.commit()
            logger.info(f"Successfully inserted user: {dict_item.get('email')}")

        except IntegrityError as e:
            session.rollback()
            logger.error(f"Integrity error inserting user {dict_item.get('email')}: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error inserting user {dict_item.get('email')}: {e}")
            raise


def get_existing_emails() -> List[str]:
    """Fetch all existing email addresses from the User table.
    
    Returns:
        List of email strings currently in the database.
    """
    with Session() as session:
        # existing_email_list = session.execute(select(User.email)).scalars().all()
        existing_email_list = list(session.scalars(select(User.email)).all())
        print("existing_email_list:", existing_email_list)
    logger.debug(f"OK Read {len(existing_email_list)} existing emails from database")
    return existing_email_list


def filter_new_users(existing_emails: List[str], input_list: list[dict]) -> list[dict]:
    """Filter input_list to only include users not already in the database.
    
    Args:
        existing_emails: List of emails already present in the database.
        input_list: Full list of user dictionaries to filter.
        
    Returns:
        List of user dictionaries that are new (not in existing_emails).
    """
    new_users_list = [
        item for item in input_list
        if item['email'] not in existing_emails
    ]
    logger.debug(f"OK Found {len(new_users_list)} new users to insert")
    return new_users_list


def insert_new_items_by_email_key(input_list: list[dict]) -> None:
    """Insert new users from input_list that don't already exist in the User table.
    
    Compares input list against existing database records and inserts only new users.
    Uses email as the unique key for comparison.
    
    Args:
        input_list: List of user dictionaries with 'email' and 'adbe_sign_id' keys.
    """
    existing_emails = get_existing_emails()
    new_users = filter_new_users(existing_emails, input_list)
    
    if new_users:
        bulk_insert_list(User, new_users)
        logger.info(f"Inserted {len(new_users)} new users")
    else:
        logger.debug("No new users to insert")
