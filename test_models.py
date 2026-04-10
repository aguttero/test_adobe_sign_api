# LOGGER CONFIG
import logging
logger = logging.getLogger(__name__)

from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import ForeignKey, Date

import datetime as dt

logger.debug("class Base creation START")
class Base (DeclarativeBase):
    pass
logger.debug("class Base creation END")

logger.debug("class User creation START")
class User(Base):
    # __tablename__ = 'user'
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
    last_sync: Mapped[dt.date] = mapped_column (Date,
                                                        default=dt.datetime.today, 
                                                        onupdate=dt.datetime.today,
                                                        nullable=False
                                                        )
    agreements: Mapped[List["Agreement"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r}, last_name={self.last_name!r})"
logger.debug("class User creation END")


class Agreement(Base):
    __tablename__ = "agreement"
    id: Mapped[int] = mapped_column(primary_key=True)
    agreement_id: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    display_date: Mapped[dt.date]
    name: Mapped[str]
    type: Mapped[str]
    status: Mapped[str]
    workflow_id: Mapped[Optional[str]]
    group_id: Mapped[str]
    created_date: Mapped [dt.date]
    last_event_date: Mapped[dt.date]

    user_id = mapped_column(ForeignKey("user_account.id"))
    
    user: Mapped[User] = relationship(back_populates="agreements")

    def __repr__(self):
        return f"Agreement(name={self.name!r}, status={self.status!r}, created_date={self.created_date!r}, id={self.id!r})"

class SyncHistory(Base):
    __tablename__ = "sync_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_date: Mapped[dt.date]
    range_start: Mapped[str]
    range_end: Mapped[str]
    agreements_found: Mapped[int] = mapped_column(default=0)
    sync_status: Mapped[bool]



logger.debug("End test Models.py")


