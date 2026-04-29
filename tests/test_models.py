"""
Data models for the Adobe Sign dashboard.
SQLAlchemy declarative models - no IO, no side effects.
"""
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import ForeignKey, Date, column
import datetime as dt
from test_utils import convert_to_sqlite_date
import logging

# Logger for this module
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class User(Base):
    """User account model mapped to user_account table."""
    __tablename__ = 'user_account'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    group_id: Mapped[Optional[int]]
    first_name: Mapped[Optional[str]]
    last_name: Mapped[Optional[str]]
    job_area: Mapped[Optional[str]]
    job_title: Mapped[Optional[str]]
    status: Mapped[Optional[str]]
    adbe_sign_id: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    last_sync: Mapped[dt.date] = mapped_column(
        Date,
        default=dt.datetime.today,
        onupdate=dt.datetime.today,
        nullable=False
    )
    
    agreements: Mapped[List["Agreement"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r}, last_name={self.last_name!r})"

class Group(Base):
    """Reference table for Adobe Sign groups."""
    __tablename__ = 'group'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    created_date: Mapped[dt.date]
    last_sync: Mapped[dt.date] = mapped_column(
        Date,
        default=dt.datetime.today,
        onupdate=dt.datetime.today,
        nullable=False
    )
    admin_email: Mapped[Optional[str]]
    is_default_grp: Mapped[bool]
    
    agreements: Mapped[List["Agreement"]] = relationship(back_populates="group")
    
    def __repr__(self) -> str:
        return f"Group(name={self.name!r}, pk_id={self.id!r}, group_id={self.group_id}, created_date={self.created_date!r}, last_sync={self.last_sync!r}, admin_email={self.admin_email!r}, is_default_grp={self.is_default_grp!r})"

class Agreement(Base):
    """Agreement model mapped to agreement table. All agreements belong to a Group."""
    __tablename__ = "agreement"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    agreement_id: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    # display_date: Mapped[dt.date]
    name: Mapped[str]
    type: Mapped[str] # Normalizar
    status: Mapped[str]
    workflow_id: Mapped[Optional[str]] # Normalizar
    group_id: Mapped[str] # Normalize
    group_id_ref: Mapped[int] = mapped_column(ForeignKey("group.id"))
    created_date: Mapped[dt.date]
    modified_date: Mapped[dt.date]
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))


    user: Mapped[User] = relationship(back_populates="agreements")

    group: Mapped[Group] = relationship(back_populates="agreements")
    
    doc_field_contents: Mapped[List["DocFieldContent"]] = relationship (
        back_populates="agreement",
        cascade="all, delete-orphan")
    signers: Mapped[List["AgreementSigner"]] = relationship(
        back_populates="agreement",
        cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Agreement(name={self.name!r}, status={self.status!r}, created_date={self.created_date!r}, id={self.id!r})"

# class Workflow(Base):
#     """Workflow model mapped to workflow table"""
#     __tablename__ = "workflow"

#     id: Mapped[int] = mapped_column(primary_key=True)
#     workflow_id: Mapped[str] = mapped_column(index=True)
#     workflow_name: Mapped[str] = mapped_column(index=True)

#     agreement: Mapped["Agreement"] = relationship(back_populates="workflow_id")
    
#     def __repr__(self) -> str:
#         return f"Workflow(name={self.workflow_name!r}, pk_id={self.id!r}, wrkflw_id={self.id!r})"
    

class DocFieldContent(Base):
    """Document field content mapped to doc_field_content table"""
    __tablename__ = "doc_field_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    agreement_id: Mapped[int] = mapped_column(ForeignKey("agreement.id"))
    agreement_subtype: Mapped [Optional[str]] # JAD CONTRATO OTRO
    requester_area: Mapped [str] = mapped_column(index=True)

    agreement: Mapped["Agreement"] = relationship(back_populates="doc_field_contents")
    
    def __repr__(self) -> str:
        return f"DocFieldContent(pk_id={self.id!r}, fk_id={self.agreement_id!r})"


class AgreementSigner(Base):
    """Agreement signer model mapped to agreement_signer table."""
    __tablename__ = "agreement_signer"

    id: Mapped[int] = mapped_column(primary_key=True)
    # agreement_id: Mapped[str] = mapped_column(nullable=False, index=True)
    agreement_id: Mapped[int] = mapped_column(ForeignKey("agreement.id"))
    signer_email: Mapped[str] = mapped_column(index=True)
    signer_full_name: Mapped[Optional[str]]
    signer_role: Mapped[str]
    signer_order: Mapped[Optional[int]]
    signature_timestamp: Mapped[Optional[str]] # quitar el nullable=False
    signature_date: Mapped [Optional[dt.date]] # quitar el nullable=False

    agreement: Mapped["Agreement"] = relationship(back_populates="signers")

    def __repr__(self) -> str:
        return f"AgreementSigner(email={self.signer_email!r}, full_name={self.signer_full_name!r}, role={self.signer_role!r})"


class SyncHistory(Base):
    """Sync history model mapped to sync_history table."""
    __tablename__ = "sync_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str]
    run_date: Mapped[dt.date]
    run_start_time: Mapped[str]
    run_end_time: Mapped[str]
    elapsed_run_time: Mapped[str]
    agrmnt_range_start: Mapped[str]
    agrmnt_range_end: Mapped[str]
    agrmnts_found: Mapped[int] = mapped_column(default=0)
    sync_ok: Mapped[bool]
    errors_found: Mapped[bool]
    warnings_found: Mapped[bool]
    critical_found: Mapped[bool]
    error_qty: Mapped[int]
    warning_qty: Mapped[int]
    critical_qty: Mapped[int]
    annotations: Mapped[Optional[str]]


def parse_groups(group_data: List[dict]) -> List[Group]:
    """Converts raw API dicts into typed Group instances."""
    #from test_utils import convert_to_sqlite_date
    parsed_groups_list =[]
    counter = 0
    for list_item in group_data:
        # Parse createdDate from ISO format
        created_date_str: str = list_item.get("createdDate", "")
        created_date = convert_to_sqlite_date(created_date_str)
        today = dt.date.today() 

        new_group = Group(
                    # id              =None,
                    group_id        =list_item.get("groupId"),
                    name            =list_item.get("groupName", ""),
                    created_date    =created_date,
                    last_sync       =today,
                    is_default_grp  =list_item.get("isDefaultGroup")
                )
        parsed_groups_list.append(new_group)
        counter +=1
    logger.debug(f"Parsed {counter} groups")
    return parsed_groups_list

def parse_agreements(api_agreement_data: List[dict], group_pk_lookup: dict[str,int]) -> List[Agreement]:
    """Parses raw API response into typed Agreement instances. Uses the group_pk_lookup dict to assign the correct group_id_ref value to Agreement instance"""
    # TODO competethis parser code
    agreement_list = []
    for dict in api_agreement_data:
        group_id = group_pk_lookup.get(dict.get("group_id"))
        if group_id is None:
            logger.warning(f"Skipping agreement {dict.get('id')} — unknown adobe_group_id")
            continue
        agreement_list.append(Agreement(
            id=dict["id"],
            name=dict["name"],
            status=dict["status"],
            group_id=group_id
        ))
    logger.debug(f"Parsed {len(agreement_list)} agreements")
    return agreement_list

def parse_agreement_signers(api_data: list[dict]) -> list[AgreementSigner]:
    """
    Extracts and flattens signer data from raw API agreements.
    Skips agreements with no signers or malformed signer records.
    """
    # TODO review, complete and test this parser code
    signers = []
    for dict in api_data:
        agreement_id = dict.get("id")
        for s in dict.get("signers", []):
            if not s.get("email"):
                logger.warning(f"Skipping malformed signer in agreement {agreement_id}")
                continue
            signers.append(AgreementSigner(
                agreement_id=agreement_id,
                email=s["email"],
                name=s.get("name", ""),
                order=s.get("order", 0),
                status=s.get("status", "unknown")
            ))
    logger.debug(f"Parsed {len(signers)} signers across {len(api_data)} agreements")
    return signers
