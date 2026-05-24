#from datetime import date
import re
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import ForeignKey, Date
import datetime as dt
import logging


logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class User(Base):
    """User account model mapped to user_account table."""
    __tablename__ = 'user_account'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    group_id: Mapped[Optional[str]]
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
    __tablename__ = "adbe_group"
    
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
        return f"Group(name={self.name!r}, pk_id={self.id!r}, group_id={self.group_id!r}, created_date={self.created_date!r}, last_sync={self.last_sync!r}, admin_email={self.admin_email!r}, is_default_grp={self.is_default_grp!r})"

class Workflow(Base):
    """Workflow model mapped to workflow table"""
    __tablename__ = "workflow"

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_id: Mapped[str] = mapped_column(unique=True, index=True)
    name_id: Mapped[str]
    name: Mapped [Optional[str]]
    description: Mapped [Optional[str]]
    status: Mapped[str]
    scope: Mapped[str]
    scope_id: Mapped[str]
    created_date:Mapped[dt.date]
    last_sync: Mapped[dt.date] = mapped_column(
        Date,
        default=dt.datetime.today,
        onupdate=dt.datetime.today,
        nullable=False
    )

    agreements: Mapped[List["Agreement"]] = relationship(back_populates="workflow")

    def __repr__(self) -> str:
        return f"Workflow(name={self.name!r}, pk_id={self.id!r}, wkflow_name_id={self.name_id!r}, wkflow_adbe_id={self.workflow_id!r}, )"

def parse_workflows(wkflow_data: List[dict]) -> List[Workflow]:
    """Converts raw API dicts into typed Group instances."""
    parsed_wkflow_list =[]
    counter = 0
    for list_item in wkflow_data:
        # Parse createdDate from ISO format
        created_date_str: str = list_item.get("created")
        created_date = convert_to_sqlite_date(created_date_str)
        today = dt.date.today() 

        new_wkflow = Workflow(
                    workflow_id=list_item.get("id"),
                    name_id=list_item.get("name"),
                    name=list_item.get("displayName", ""),
                    description=list_item.get("description", ""),
                    status=list_item.get("status"),
                    scope=list_item.get("scope"),
                    scope_id=list_item.get("scopeId"),
                    created_date=created_date,
                    last_sync=today,
                )
        parsed_wkflow_list.append(new_wkflow)
        counter +=1
    logger.debug(f"Parsed {counter} workflows")
    return parsed_wkflow_list

class Agreement(Base):
    """Agreement model mapped to agreement table. All agreements belong to a Group."""
    __tablename__ = "agreement"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    agreement_id: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    # display_date: Mapped[dt.date]
    name: Mapped[str]
    type: Mapped[str] # Normalize
    status: Mapped[str]
    # workflow_id: Mapped[Optional[str]] # Normalize
    # group_id: Mapped[str] # Normalize
    group_id_ref: Mapped[Optional[int]] = mapped_column(ForeignKey("adbe_group.id"))
    workflow_id_ref: Mapped[Optional[int]] = mapped_column(ForeignKey("workflow.id"))
    created_date: Mapped[dt.date]
    modified_date: Mapped[dt.date]
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))


    user: Mapped[User] = relationship(back_populates="agreements")

    group: Mapped[Optional[Group]] = relationship(back_populates="agreements")
    workflow: Mapped[Optional[Workflow]] = relationship(back_populates="agreements")
    
    # Document field content relationship
    doc_field_contents: Mapped[List["DocFieldContent"]] = relationship (
        back_populates="agreement",
        cascade="all, delete-orphan")
    signers: Mapped[List["AgreementSigner"]] = relationship(
        back_populates="agreement",
        cascade="all, delete-orphan")
    # Document donwload relationship
    document: Mapped["Document"] = relationship(back_populates="agreement")

    def __repr__(self) -> str:
        return f"Agreement(name={self.name!r}, status={self.status!r}, created_date={self.created_date!r}, id={self.id!r})"

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

class Document(Base):
    """Downloaded document information table"""
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(primary_key=True)
    agreement_id: Mapped[int] = mapped_column(ForeignKey("agreement.id"))
    agreemen_type: Mapped [str] # JAD CONTRATO OTRO
    pdf_file_path: Mapped[Optional[str]]
    txt_file_path: Mapped[Optional[str]]
    file_size_bytes: Mapped[Optional[int]]
    downloaded_ts: Mapped[Optional[str]]
    file_status: Mapped[str] = mapped_column(default="pending") #lifecycle status for pdf and txt
    # file_status: Mapped[str] = mapped_column(
    #     str,
    #     CheckConstraint("file_status IN ('pending', 'downloaded', 'parsed', 'purged_pdf', 'purged_full' )"),
    #     server_default="pending",
    #     nullable=False
    # )
    parsed_ts: Mapped[Optional[str]]
    pdf_purged_ts: Mapped[Optional[str]]
    txt_purged_ts: Mapped[Optional[str]]
    error_message: Mapped[Optional[str]]

    agreement: Mapped["Agreement"] = relationship(back_populates="document")
    
    def __repr__(self) -> str:
        return f"Document(pk_id={self.id!r}, fk_id={self.agreement_id!r}, file_path={self.file_path!r})"


def parse_agreements_v1(api_agreement_data: List[dict], group_pk_lookup: dict[str,int]) -> List[Agreement]:
    """Parses raw API response into typed Agreement instances. Uses the group_pk_lookup dict to assign the correct group_id_ref value to Agreement instance"""
    agreement_list = []
    for item in api_agreement_data:
        group_id_ref = group_pk_lookup.get(item.get("groupId"))
        if group_id_ref is None:
            logger.warning(f"Skipping agreement {item.get('id')} — unknown adobe_group_id")
            continue
        
        created_date_str = item.get("createdDate", "")
        created_date = convert_to_sqlite_date(created_date_str)
        
        modified_date_str = item.get("modifiedDate", "")
        modified_date = convert_to_sqlite_date(modified_date_str)
        
        # Extract document field content
        doc_field_contents_data = item.get("docFieldList", [])
        doc_field_contents = []
        if doc_field_contents_data:
            for field in doc_field_contents_data:
                doc_field_contents.append(DocFieldContent(
                    agreement_id=item.get("id"), # This will be the Agreement's ID after it's created
                    agreement_subtype=field.get("subType"),
                    requester_area=field.get("defaultValue", ""), # Assuming defaultValue contains relevant info
                ))

        agreement_list.append(Agreement(
            agreement_id=item.get("id"),
            name=item.get("name"),
            type="AGREEMENT",
            status=item.get("status"),
            workflow_id=item.get("workflowId"),
            group_id=item.get("groupId"),
            group_id_ref=group_id_ref,
            created_date=created_date,
            modified_date=modified_date,
            user_id=item.get("userId"),
            doc_field_contents=doc_field_contents # Assign extracted doc field contents
        ))
    logger.debug(f"Parsed {len(agreement_list)} agreements")
    return agreement_list

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
    run_id: Mapped[str] = mapped_column(index=True)
    run_date: Mapped[dt.date]
    run_start_time: Mapped[str]
    run_end_time: Mapped[str]
    elapsed_run_time: Mapped[str]
    agrmnt_range_start: Mapped[str]
    agrmnt_range_end: Mapped[str]
    new_agrmnts: Mapped[int] = mapped_column(default=0)
    new_users: Mapped[int] = mapped_column(default=0)
    new_groups: Mapped[int] = mapped_column(default=0)
    new_wkflows: Mapped[int] = mapped_column(default=0)
    sync_ok: Mapped[bool]
    errors_found: Mapped[bool]
    warnings_found: Mapped[bool]
    critical_found: Mapped[bool]
    error_qty: Mapped[int]
    warning_qty: Mapped[int]
    critical_qty: Mapped[int]
    annotations: Mapped[Optional[str]]

def convert_to_sqlite_date(date_iso: str) -> dt.date:
    """Convert ISO date string to SQLite date format.
    
    Args:
        date_iso: ISO format date string (e.g., "2026-03-02T08:23:52-08:00")
        
    Returns:
        Date object.
    """
    dt_obj = dt.datetime.fromisoformat(date_iso)
    date_sqlite = dt_obj.date()
    return date_sqlite

def parse_groups(group_data: List[dict]) -> List[Group]:
    """Converts raw API dicts into typed Group instances."""
    
    parsed_groups_list =[]
    counter = 0
    for list_item in group_data:
        # Parse createdDate from ISO format
        created_date_str: str = list_item.get("createdDate")
        created_date = convert_to_sqlite_date(created_date_str)
        today = dt.date.today() 

        new_group = Group(
                    group_id=list_item.get("groupId"),
                    name=list_item.get("groupName", ""),
                    created_date=created_date,
                    last_sync=today,
                    is_default_grp=list_item.get("isDefaultGroup")
                )
        parsed_groups_list.append(new_group)
        # logger.debug(f"parsed_new_group={new_group}")
        counter +=1
    logger.debug(f"Parsed {counter} groups")
    return parsed_groups_list

def parse_agreements_v0 (api_agreement_data: List[dict], group_pk_lookup: dict[str,int]) -> List[Agreement]:
    """Parses raw API response into typed Agreement instances. Uses the group_pk_lookup dict to assign the correct group_id_ref value to Agreement instance"""
    agreement_list = []
    for item in api_agreement_data:
        group_id_ref = group_pk_lookup.get(item.get("groupId"))
        if group_id_ref is None:
            logger.warning(f"Skipping agreement {item.get('id')} — unknown adobe_group_id")
            continue
        
        created_date_str = item.get("createdDate", "")
        created_date = convert_to_sqlite_date(created_date_str)
        
        modified_date_str = item.get("modifiedDate", "")
        modified_date = convert_to_sqlite_date(modified_date_str)

        agreement_list.append(Agreement(
            agreement_id=item.get("id"),
            name=item.get("name"),
            type="AGREEMENT",
            status=item.get("status"),
            workflow_id=item.get("workflowId"),
            group_id=item.get("groupId"),
            group_id_ref=group_id_ref,
            created_date=created_date,
            modified_date=modified_date,
            user_id=item.get("userId")
        ))
    logger.debug(f"Parsed {len(agreement_list)} agreements")
    return agreement_list

def parse_agreement_signers(api_data: list[dict]) -> list[AgreementSigner]:
    """
    Extracts and flattens signer data from raw API agreements.
    Skips agreements with no signers or malformed signer records.
    """
    signers = []
    for item in api_data:
        agreement_id = item.get("id")
        for participant in item.get("participantList", []):
            if not participant.get("email"):
                logger.warning(f"Skipping malformed signer in agreement {agreement_id}")
                continue
            
            roles = participant.get("role", [])
            signers.append(AgreementSigner(
                agreement_id=agreement_id,
                signer_email=participant.get("email"),
                signer_full_name=participant.get("fullName", ""),
                signer_role=roles[0] if roles else "",
                signer_order=participant.get("order")
            ))
    logger.debug(f"Parsed {len(signers)} signers across {len(api_data)} agreements")
    return signers
