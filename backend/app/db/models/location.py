"""Dealership location model sourced from ``z_locations.csv``."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Location(Base):
    __tablename__ = "locations"

    location_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_group: Mapped[int | None] = mapped_column(Integer)
    booking_hub: Mapped[int | None] = mapped_column(Integer)
    cluster_id: Mapped[int | None] = mapped_column(Integer)
    location_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    location_name: Mapped[str | None] = mapped_column(String(128))
    location_dms: Mapped[str | None] = mapped_column(String(160))
    outlet_type_raw: Mapped[str | None] = mapped_column(String(64))
    outlet_type: Mapped[str | None] = mapped_column(String(64), index=True)
    outlet_function_raw: Mapped[str | None] = mapped_column(String(64))
    outlet_function: Mapped[str | None] = mapped_column(String(64))
    location_status: Mapped[int | None] = mapped_column(Integer)
    location_added_datetime: Mapped[datetime | None] = mapped_column(DateTime)
    latlng: Mapped[str | None] = mapped_column(String(128))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

