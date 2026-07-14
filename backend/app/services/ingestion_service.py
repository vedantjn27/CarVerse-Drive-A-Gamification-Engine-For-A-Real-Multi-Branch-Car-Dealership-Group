"""Validated, idempotent ingestion of the three organizer-provided CSV files."""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from itertools import islice
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.models import Employee, Location, RawEvent
from app.db.session import engine


EVENT_FILE = "z_event_log_may_june_2026.csv"
EMPLOYEE_FILE = "z_employees.csv"
LOCATION_FILE = "z_locations.csv"

EVENT_HEADERS = (
    "id",
    "group_id",
    "stage",
    "categories",
    "department",
    "username",
    "user_id",
    "enquiry_no",
    "location_code",
    "message",
    "action_code",
    "source",
    "created_date",
)
EMPLOYEE_HEADERS = (
    "group_id",
    "id",
    "name",
    "mobile",
    "loc_code",
    "reporting_location",
    "designation",
    "manager",
    "dse_code",
    "department",
    "role_rights",
    "alt_id",
    "logout",
    "manager_id",
    "otp",
    "status",
    "created_date",
    "role",
    "last_active_time",
    "assigned_locations",
    "telegram_chat_id",
    "webauth_security",
    "no_of_device_allowed",
)
LOCATION_HEADERS = (
    "location_id",
    "location_group",
    "booking_hub",
    "cluster_id",
    "location_code",
    "location_name",
    "location_dms",
    "outlet_type",
    "outlet_function",
    "location_status",
    "location_added_datetime",
    "latlng",
)

DEPARTMENT_ALIASES = {
    "CCM": "CUSTOMER CARE",
    "RTO": "RTO / REGN TEAM",
}
ACTION_PREFIX_ALIASES = {
    "RGISTRATION": "REGISTRATION",
    "REGISTARTION": "REGISTRATION",
}
NULL_STRINGS = {"", "NULL"}
DOCUMENTS_OTHER_PATTERN = re.compile(r"^DOCUMENTS_OTHER(?:\s*-.*)?$")


class IngestionError(RuntimeError):
    """Raised when an organizer file violates the expected data contract."""


@dataclass(frozen=True, slots=True)
class FileIngestionStats:
    filename: str
    rows_read: int
    rows_inserted: int
    rows_skipped: int


@dataclass(frozen=True, slots=True)
class IngestionSummary:
    locations: FileIngestionStats
    employees: FileIngestionStats
    events: FileIngestionStats

    @property
    def total_rows_read(self) -> int:
        return sum(item.rows_read for item in self.files)

    @property
    def total_rows_inserted(self) -> int:
        return sum(item.rows_inserted for item in self.files)

    @property
    def total_rows_skipped(self) -> int:
        return sum(item.rows_skipped for item in self.files)

    @property
    def files(self) -> tuple[FileIngestionStats, ...]:
        return (self.locations, self.employees, self.events)


def clean_nullable(value: str | None) -> str | None:
    """Trim a CSV value and convert the export's null sentinel to ``None``."""

    if value is None:
        return None
    cleaned = value.strip()
    if cleaned.upper() in NULL_STRINGS:
        return None
    return cleaned


def normalize_token(value: str | None) -> str | None:
    """Uppercase, trim, and collapse whitespace in a categorical value."""

    cleaned = clean_nullable(value)
    if cleaned is None:
        return None
    return re.sub(r"\s+", " ", cleaned).upper()


def normalize_department(value: str | None) -> str | None:
    normalized = normalize_token(value)
    if normalized is None:
        return None
    return DEPARTMENT_ALIASES.get(normalized, normalized)


def normalize_action_code(value: str | None) -> str:
    """Create a stable scoring key while retaining the raw code separately."""

    normalized = normalize_token(value)
    if normalized is None:
        raise IngestionError("action_code cannot be blank")

    for misspelling, canonical in ACTION_PREFIX_ALIASES.items():
        if normalized == misspelling or normalized.startswith(f"{misspelling}_"):
            normalized = canonical + normalized[len(misspelling) :]
            break

    if DOCUMENTS_OTHER_PATTERN.fullmatch(normalized):
        return "DOCUMENTS_OTHER"
    return normalized


def _required(value: str | None, field: str) -> str:
    cleaned = clean_nullable(value)
    if cleaned is None:
        raise IngestionError(f"{field} cannot be blank")
    return cleaned


def _integer(value: str | None, field: str, *, required: bool = False) -> int | None:
    cleaned = clean_nullable(value)
    if cleaned is None:
        if required:
            raise IngestionError(f"{field} cannot be blank")
        return None
    try:
        return int(cleaned)
    except ValueError as exc:
        raise IngestionError(f"{field} must be an integer, got {cleaned!r}") from exc


def _timestamp(
    value: str | None, field: str, *, required: bool = False
) -> datetime | None:
    cleaned = clean_nullable(value)
    if cleaned is None:
        if required:
            raise IngestionError(f"{field} cannot be blank")
        return None
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise IngestionError(f"{field} has an invalid timestamp: {cleaned!r}") from exc


def _coordinates(value: str | None) -> tuple[float | None, float | None]:
    cleaned = clean_nullable(value)
    if cleaned is None:
        return None, None
    parts = [part.strip() for part in cleaned.split(",")]
    if len(parts) != 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def _csv_rows(path: Path, expected_headers: tuple[str, ...]) -> Iterator[dict[str, str]]:
    if not path.is_file():
        raise IngestionError(f"Required organizer file is missing: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual_headers = tuple(reader.fieldnames or ())
        if actual_headers != expected_headers:
            raise IngestionError(
                f"Unexpected headers in {path.name}: expected {expected_headers}, "
                f"got {actual_headers}"
            )
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise IngestionError(
                    f"Malformed row {row_number} in {path.name}: extra CSV fields"
                )
            try:
                yield row
            except IngestionError as exc:
                raise IngestionError(
                    f"Invalid row {row_number} in {path.name}: {exc}"
                ) from exc


def _location_records(path: Path) -> Iterator[dict[str, Any]]:
    for row in _csv_rows(path, LOCATION_HEADERS):
        latitude, longitude = _coordinates(row["latlng"])
        outlet_type_raw = clean_nullable(row["outlet_type"])
        outlet_function_raw = clean_nullable(row["outlet_function"])
        yield {
            "location_id": _integer(row["location_id"], "location_id", required=True),
            "location_group": _integer(row["location_group"], "location_group"),
            "booking_hub": _integer(row["booking_hub"], "booking_hub"),
            "cluster_id": _integer(row["cluster_id"], "cluster_id"),
            "location_code": _required(row["location_code"], "location_code").upper(),
            "location_name": clean_nullable(row["location_name"]),
            "location_dms": clean_nullable(row["location_dms"]),
            "outlet_type_raw": outlet_type_raw,
            "outlet_type": normalize_token(outlet_type_raw),
            "outlet_function_raw": outlet_function_raw,
            "outlet_function": normalize_token(outlet_function_raw),
            "location_status": _integer(row["location_status"], "location_status"),
            "location_added_datetime": _timestamp(
                row["location_added_datetime"], "location_added_datetime"
            ),
            "latlng": clean_nullable(row["latlng"]),
            "latitude": latitude,
            "longitude": longitude,
        }


def _employee_records(path: Path) -> Iterator[dict[str, Any]]:
    for row in _csv_rows(path, EMPLOYEE_HEADERS):
        department_raw = clean_nullable(row["department"])
        status_raw = clean_nullable(row["status"])
        yield {
            "group_id": _integer(row["group_id"], "group_id"),
            "id": _required(row["id"], "id"),
            "name": clean_nullable(row["name"]),
            "mobile": clean_nullable(row["mobile"]),
            "loc_code": normalize_token(row["loc_code"]),
            "reporting_location": clean_nullable(row["reporting_location"]),
            "designation": clean_nullable(row["designation"]),
            "manager": clean_nullable(row["manager"]),
            "dse_code": clean_nullable(row["dse_code"]),
            "department_raw": department_raw,
            "department": normalize_department(department_raw),
            "role_rights": clean_nullable(row["role_rights"]),
            "alt_id": clean_nullable(row["alt_id"]),
            "logout": clean_nullable(row["logout"]),
            "manager_id": clean_nullable(row["manager_id"]),
            "otp": clean_nullable(row["otp"]),
            "status_raw": status_raw,
            "status": _integer(status_raw, "status"),
            "created_date": _timestamp(row["created_date"], "created_date"),
            "role": clean_nullable(row["role"]),
            "last_active_time": _timestamp(
                row["last_active_time"], "last_active_time"
            ),
            "assigned_locations": clean_nullable(row["assigned_locations"]),
            "telegram_chat_id": clean_nullable(row["telegram_chat_id"]),
            "webauth_security": clean_nullable(row["webauth_security"]),
            "no_of_device_allowed": _integer(
                row["no_of_device_allowed"], "no_of_device_allowed"
            ),
        }


def _event_records(path: Path) -> Iterator[dict[str, Any]]:
    for row in _csv_rows(path, EVENT_HEADERS):
        enquiry_no_raw = _required(row["enquiry_no"], "enquiry_no")
        location_code_raw = _required(row["location_code"], "location_code")
        enquiry_no = None if enquiry_no_raw == "-" else enquiry_no_raw
        location_code = None if location_code_raw == "-" else location_code_raw.upper()
        if (enquiry_no is None) != (location_code is None):
            raise IngestionError(
                "enquiry_no and location_code must both identify a booking or both be '-'"
            )

        action_code_raw = _required(row["action_code"], "action_code")
        stage_raw = _required(row["stage"], "stage")
        categories_raw = _required(row["categories"], "categories")
        department_raw = _required(row["department"], "department")
        source_raw = _required(row["source"], "source")
        yield {
            "id": _integer(row["id"], "id", required=True),
            "group_id": _integer(row["group_id"], "group_id"),
            "stage_raw": stage_raw,
            "stage": normalize_token(stage_raw),
            "categories_raw": categories_raw,
            "categories": normalize_token(categories_raw),
            "department_raw": department_raw,
            "department": normalize_department(department_raw),
            "username": clean_nullable(row["username"]),
            "user_id": _required(row["user_id"], "user_id"),
            "enquiry_no_raw": enquiry_no_raw,
            "enquiry_no": enquiry_no,
            "location_code_raw": location_code_raw,
            "location_code": location_code,
            "message": clean_nullable(row["message"]),
            "action_code_raw": action_code_raw,
            "action_code": normalize_action_code(action_code_raw),
            "source_raw": source_raw,
            "source": normalize_token(source_raw),
            "created_date": _timestamp(
                row["created_date"], "created_date", required=True
            ),
        }


def _batched(
    records: Iterable[Mapping[str, Any]], batch_size: int
) -> Iterator[list[Mapping[str, Any]]]:
    iterator = iter(records)
    while batch := list(islice(iterator, batch_size)):
        yield batch


async def _insert_idempotently(
    session: AsyncSession,
    model: type[Location] | type[Employee] | type[RawEvent],
    records: Iterable[Mapping[str, Any]],
    conflict_column: str,
    batch_size: int,
    assume_empty: bool,
) -> tuple[int, int]:
    rows_read = 0
    rows_inserted = 0
    seen_values: set[Any] = set()
    for batch in _batched(records, batch_size):
        conflict_values = [row[conflict_column] for row in batch]
        existing_values: set[Any] = set()
        if not assume_empty:
            conflict_attribute = getattr(model, conflict_column)
            existing_values = set(
                (
                    await session.execute(
                        select(conflict_attribute).where(
                            conflict_attribute.in_(conflict_values)
                        )
                    )
                ).scalars()
            )
        new_rows = []
        for row in batch:
            value = row[conflict_column]
            if value not in existing_values and value not in seen_values:
                new_rows.append(row)
                seen_values.add(value)
        if new_rows:
            statement = sqlite_insert(model).on_conflict_do_nothing(
                index_elements=[conflict_column]
            )
            await session.execute(statement, new_rows)
        rows_read += len(batch)
        rows_inserted += len(new_rows)
    return rows_read, rows_inserted


async def _ingest_file(
    session: AsyncSession,
    *,
    filename: str,
    model: type[Location] | type[Employee] | type[RawEvent],
    records: Iterable[Mapping[str, Any]],
    conflict_column: str,
    batch_size: int,
    assume_empty: bool,
) -> FileIngestionStats:
    async with session.begin():
        rows_read, rows_inserted = await _insert_idempotently(
            session, model, records, conflict_column, batch_size, assume_empty
        )
    return FileIngestionStats(
        filename=filename,
        rows_read=rows_read,
        rows_inserted=rows_inserted,
        rows_skipped=rows_read - rows_inserted,
    )


def validate_dataset_files(data_directory: Path) -> None:
    """Fail before schema reset if any required input is missing or has bad headers."""

    contracts = (
        (LOCATION_FILE, LOCATION_HEADERS),
        (EMPLOYEE_FILE, EMPLOYEE_HEADERS),
        (EVENT_FILE, EVENT_HEADERS),
    )
    for filename, expected_headers in contracts:
        path = data_directory / filename
        if not path.is_file():
            raise IngestionError(f"Required organizer file is missing: {path}")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            actual_headers = tuple(csv.DictReader(handle).fieldnames or ())
        if actual_headers != expected_headers:
            raise IngestionError(
                f"Unexpected headers in {filename}: expected {expected_headers}, "
                f"got {actual_headers}"
            )


async def ingest_all(
    session: AsyncSession,
    data_directory: Path,
    *,
    batch_size: int | None = None,
    assume_empty: bool = False,
) -> IngestionSummary:
    """Ingest all source files in dependency order without duplicating rows."""

    validate_dataset_files(data_directory)
    size = batch_size or settings.ingest_batch_size
    locations = await _ingest_file(
        session,
        filename=LOCATION_FILE,
        model=Location,
        records=_location_records(data_directory / LOCATION_FILE),
        conflict_column="location_code",
        batch_size=size,
        assume_empty=assume_empty,
    )
    employees = await _ingest_file(
        session,
        filename=EMPLOYEE_FILE,
        model=Employee,
        records=_employee_records(data_directory / EMPLOYEE_FILE),
        conflict_column="id",
        batch_size=size,
        assume_empty=assume_empty,
    )
    events = await _ingest_file(
        session,
        filename=EVENT_FILE,
        model=RawEvent,
        records=_event_records(data_directory / EVENT_FILE),
        conflict_column="id",
        batch_size=size,
        assume_empty=assume_empty,
    )
    return IngestionSummary(locations=locations, employees=employees, events=events)


async def reset_schema_and_seed(data_directory: Path) -> IngestionSummary:
    """Validate inputs, recreate the disposable schema, and seed every CSV row."""

    validate_dataset_files(data_directory)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        return await ingest_all(session, data_directory, assume_empty=True)
