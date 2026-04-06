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
    first_name: Mapped[Optional[str]]
    last_name: Mapped[Optional[str]]
    job_area: Mapped[Optional[str]]
    job_title: Mapped[Optional[str]]
    status: Mapped[Optional[str]]
    sign_user_id: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    #last_sync = Column(Date, default=dt.datetime.today(), onupdate=dt.datetime.today())
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
    agreement_id: Mapped[str]
    name: Mapped[str]
    status: Mapped[str]
    created_date: Mapped [dt.date]
    user_id = mapped_column(ForeignKey("user_account.id"))
    
    user: Mapped[User] = relationship(back_populates="agreements")

    def __repr__(self):
        return f"Agreement(name={self.name!r}, status={self.status!r}, created_date={self.created_date!r}, id={self.id!r})"

logger.debug("End test Models.py")


