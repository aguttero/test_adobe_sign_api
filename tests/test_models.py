"""
Data models for the Adobe Sign dashboard.
SQLAlchemy declarative models - no IO, no side effects.
"""
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import ForeignKey, Date
import datetime as dt


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class User(Base):
    """User account model mapped to user_account table."""
    __tablename__ = 'user_account'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
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


class Agreement(Base):
    """Agreement model mapped to agreement table."""
    __tablename__ = "agreement"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    agreement_id: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    # display_date: Mapped[dt.date]
    name: Mapped[str]
    type: Mapped[str]
    keyword: Mapped[Optional[str]] = mapped_column (index=True)
    status: Mapped[str]
    workflow_id: Mapped[Optional[str]]
    group_id: Mapped[str]
    created_date: Mapped[dt.date]
    modified_date: Mapped[dt.date]

    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))

    user: Mapped[User] = relationship(back_populates="agreements")
    signers: Mapped[List["AgreementSigner"]] = relationship(
        back_populates="agreement",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Agreement(name={self.name!r}, status={self.status!r}, created_date={self.created_date!r}, id={self.id!r})"


class AgreementSigner(Base):
    """Agreement signer model mapped to agreement_signer table."""
    __tablename__ = "agreement_signer"

    id: Mapped[int] = mapped_column(primary_key=True)
    # agreement_id: Mapped[str] = mapped_column(nullable=False, index=True)
    agreement_id: Mapped[int] = mapped_column(ForeignKey("agreement.id"))
    signer_email: Mapped[str] = mapped_column(nullable=False, index=True)
    signer_full_name: Mapped[Optional[str]]
    signer_role: Mapped[Optional[str]]
    signer_order: Mapped[Optional[int]]

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