"""Employee model sourced from ``z_employees.csv``."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_department_location", "department", "loc_code"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    group_id: Mapped[int | None] = mapped_column(Integer)
    name: Mapped[str | None] = mapped_column(String(160), index=True)
    mobile: Mapped[str | None] = mapped_column(String(32))
    loc_code: Mapped[str | None] = mapped_column(String(32), index=True)
    reporting_location: Mapped[str | None] = mapped_column(String(160))
    designation: Mapped[str | None] = mapped_column(String(160))
    manager: Mapped[str | None] = mapped_column(String(160))
    dse_code: Mapped[str | None] = mapped_column(String(64))
    department_raw: Mapped[str | None] = mapped_column(String(64))
    department: Mapped[str | None] = mapped_column(String(64), index=True)
    role_rights: Mapped[str | None] = mapped_column(Text)
    alt_id: Mapped[str | None] = mapped_column(String(64))
    logout: Mapped[str | None] = mapped_column(String(64))
    manager_id: Mapped[str | None] = mapped_column(String(64), index=True)
    otp: Mapped[str | None] = mapped_column(String(32))
    status_raw: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[int | None] = mapped_column(Integer, index=True)
    created_date: Mapped[datetime | None] = mapped_column(DateTime)
    role: Mapped[str | None] = mapped_column(String(32), index=True)
    last_active_time: Mapped[datetime | None] = mapped_column(DateTime)
    assigned_locations: Mapped[str | None] = mapped_column(Text)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64))
    webauth_security: Mapped[str | None] = mapped_column(Text)
    no_of_device_allowed: Mapped[int | None] = mapped_column(Integer)

