"""
Database operations for the Adobe Sign dashboard.
All database access via SQLAlchemy. No API calls, no token logic.
"""
from datetime import date, datetime
import logging
from typing import List, Type

from sqlalchemy import create_engine, select, insert
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from test_models import Base, User, Agreement, AgreementSigner
from test_exceptions import DatabaseError


logger = logging.getLogger(__name__)

# Lazy engine initialization
_engine = None


def _get_engine():
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        DB_ENGINE_URL = "sqlite:///tests/data/test_01.db"
        _engine = create_engine(DB_ENGINE_URL, echo=True)
        Base.metadata.create_all(_engine)
        logger.debug("DB engine get or create OK")
    return _engine


def _get_session() -> Session:
    """Create a new database session."""
    logger.debug("DB Session created OK")
    return sessionmaker(bind=_get_engine())()


def test_update_user_status_by_email(searched_email: str, new_status: str) -> None:
    """Updates status field of single user by email key."""
    with _get_session() as session:
        try:
            stmt = select(User).filter_by(email=searched_email)
            user = session.execute(stmt).scalar_one_or_none()

            if user:
                user.status = new_status
                session.commit()
                logger.debug("update ok")
            else:
                logger.debug(f"usuario {searched_email} no encontrado")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to update user status: {e}")
            raise DatabaseError(f"Failed to update user status: {e}", original_exc=e)


def test_update_users(user_list: List[dict]) -> None:
    """Upserts User table using email as the natural key.
    
    Uses session.merge to INSERT new users (email not yet in DB)
    or UPDATE existing users (matched by email).
    
    Args:
        user_list: List of dicts with 'email' and 'adbe_sign_id' keys.
    """
    with _get_session() as session:
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
            raise DatabaseError(f"Failed to upsert users: {e}", original_exc=e)


def test_convert_txt_to_list(filename: str) -> List[dict]:
    """Converts file.txt user list to python list.
    
    Args:
        filename: Path to the text file containing user list.
        
    Returns:
        List of user dictionaries parsed from file.
    """
    import ast
    
    try:
        with open(filename, "r") as file:
            file_content = file.read()
            logger.debug(f"OK Read: {filename} - {len(file_content)} chars")

        user_list = ast.literal_eval(file_content)
        logger.debug(f"OK Assign to list {len(user_list)} items")
        return user_list
    except Exception as e:
        logger.error(f"Failed to read user list file: {e}")
        raise DatabaseError(f"Failed to read user list file: {e}", original_exc=e)


def transform_user_list_keys(input_list: List[dict]) -> List[dict]:
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


def bulk_insert_list(table_name: Type[Base], input_list: List[dict]) -> None:
    """Bulk insert input_list into table for initial table load.
    
    Args:
        table_name: The SQLAlchemy model class to insert into.
        input_list: List of dictionaries representing rows to insert.
    """
    with _get_session() as session:
        try:
            session.execute(insert(table_name), input_list)
            session.commit()
            logger.info(f"OK insert {len(input_list)} records into {table_name.__name__}")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"SQLA error during bulk insert: {e}")
            raise DatabaseError(f"SQLA error during bulk insert: {e}", original_exc=e)


def get_existing_emails() -> List[str]:
    """Fetch all existing email addresses from the User table.
    
    Returns:
        List of email strings currently in the database.
    """
    with _get_session() as session:
        try:
            existing_email_list = list(session.scalars(select(User.email)).all())
            logger.debug(f"Fetched {len(existing_email_list)} emails from database")
            return existing_email_list
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch existing emails: {e}")
            raise DatabaseError(f"Failed to fetch existing emails: {e}", original_exc=e)


def filter_new_users(existing_emails: List[str], input_list: List[dict]) -> List[dict]:
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


def insert_new_items_by_email_key(input_list: List[dict]) -> None:
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


def get_user_by_email(user_email: str) -> User:
    """Fetch a user by email address.

    Args:
        user_email: Email address to search for.

    Returns:
        User object if found, None otherwise.
    """
    with _get_session() as session:
        try:
            stmt = select(User).filter_by(email=user_email)
            user = session.execute(stmt).scalar_one_or_none()
            logger.debug(f"Fetched user: {user_email}")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch user by email: {e}")
            raise DatabaseError(f"Failed to fetch user by email: {e}", original_exc=e)


def get_user_by_adbe_sign_id(adbe_sign_id: str) -> User:
    """Fetch a user by Adobe Sign ID.

    Args:
        adbe_sign_id: Adobe Sign user ID to search for.

    Returns:
        User object if found, None otherwise.
    """
    with _get_session() as session:
        try:
            stmt = select(User).filter_by(adbe_sign_id=adbe_sign_id)
            user = session.execute(stmt).scalar_one_or_none()
            logger.debug(f"Fetched user by adbe_sign_id: {adbe_sign_id}")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch user by adbe_sign_id: {e}")
            raise DatabaseError(f"Failed to fetch user by adbe_sign_id: {e}", original_exc=e)


def _parse_date(date_str: str) -> date:
    """Parse date string to YYYY-MM-DD format for SQLite.

    Args:
        date_str: Date string from API (e.g., "2020-06-16T07:20:31-07:00").

    Returns:
        Date string in YYYY-MM-DD format.
    """
    #logger.debug(f"input date value: {date_str}")
    # Convert string to date object
    date_time_obj = datetime.fromisoformat(date_str)

    # Convert naive date + time to date object
    date_obj = date_time_obj.date()
    #logger.debug(f"output date value: {date_obj}")
    return date_obj
    # Extract date part (first 10 characters)
#    return date_str[:10]


def insert_agreements(agreement_list: List[dict], user_id: int) -> int:
    """Insert agreements and their signers into the database.

    Args:
        agreement_list: List of agreement dictionaries from API.
        user_id: User ID to associate agreements with.

    Returns:
        Number of agreements inserted.
    """
    if not agreement_list:
        logger.debug("No agreements to insert")
        return 0

    agreements_inserted: int = 0

    with _get_session() as session:
        try:
            for agr in agreement_list:
                # Check if agreement already exists (by agreement_id)
                stmt = select(Agreement).filter_by(agreement_id=agr.get("agreement_id"))
                existing = session.execute(stmt).scalar_one_or_none()

                if existing:
                    logger.debug(f"Agreement {agr.get('agreement_id')} already exists, skipping")
                    continue

                # Create agreement record
                new_agreement = Agreement(
                    agreement_id=agr.get("agreement_id"),
                    # display_date=_parse_date(agr.get("created_date", "")),
                    name=agr.get("name", ""),
                    type="AGREEMENT",
                    status=agr.get("status", ""),
                    workflow_id=agr.get("workflow_id", ""),
                    group_id=agr.get("group_id", ""),
                    created_date=_parse_date(agr.get("created_date", "")),
                    modified_date=_parse_date(agr.get("modified_date", "")),
                    user_id=user_id
                )
                session.add(new_agreement)
                session.flush()  # Get the agreement ID

                # Insert signers for this agreement
                signers = agr.get("signers", [])
                for signer in signers:
                    new_signer = AgreementSigner(
                        # agreement_id=agr.get("agreement_id"),
                        agreement_id=new_agreement.id,
                        signer_email=signer.get("signer_email", ""),
                        signer_full_name=signer.get("signer_full_name", ""),
                        signer_role=signer.get("signer_role", "")
                    )
                    session.add(new_signer)

                agreements_inserted += 1

            session.commit()
            logger.info(f"Inserted {agreements_inserted} agreements")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to insert agreements: {e}")
            raise DatabaseError(f"Failed to insert agreements: {e}", original_exc=e)

    return agreements_inserted


def agreement_exists(agreement_id: str) -> bool:
    """Check if an agreement already exists in the database.

    Args:
        agreement_id: The agreement ID to check.

    Returns:
        True if exists, False otherwise.
    """
    with _get_session() as session:
        try:
            stmt = select(Agreement).filter_by(agreement_id=agreement_id)
            exists = session.execute(stmt).scalar_one_or_none() is not None
            return exists
        except SQLAlchemyError as e:
            logger.error(f"Failed to check agreement existence: {e}")
            raise DatabaseError(f"Failed to check agreement existence: {e}", original_exc=e)