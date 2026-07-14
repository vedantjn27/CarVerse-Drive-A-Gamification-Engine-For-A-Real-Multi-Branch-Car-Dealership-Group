"""Compact, deterministic data for normal API tests; never replaces full-data checks."""

from datetime import datetime

from app.db.base import Base
from app.db.models import Employee, Location, RawEvent
from app.db.session import AsyncSessionFactory, engine
from app.services.gamification_service import materialize_gamification
from app.services.scoring_engine import score_all_events
from app.services.quest_service import seed_quest_templates
from app.services.boss_battle_service import materialize_boss_battles


TEST_DATABASE_PATH = "data/test_carverse.db"


def _employee(user_id: str, name: str, department: str, location: str, role_rights: str = "AGENT") -> Employee:
    return Employee(id=user_id, group_id=1, name=name, mobile=None, loc_code=location, reporting_location=None, designation="Executive", manager=None, dse_code=None, department_raw=department, department=department, role_rights=role_rights, alt_id=None, logout=None, manager_id=None, otp=f"otp-{user_id}", status_raw="1", status=1, created_date=datetime(2026, 1, 1), role=None, last_active_time=None, assigned_locations=None, telegram_chat_id=None, webauth_security=None, no_of_device_allowed=1)


def _event(event_id: int, user_id: str, department: str, action: str, created: datetime, enquiry: str | None = None, location: str | None = None, stage: str = "PENDING-BOOKING") -> RawEvent:
    return RawEvent(id=event_id, group_id=1, stage_raw=stage, stage=stage, categories_raw="TEST", categories="TEST", department_raw=department, department=department, username=user_id, user_id=user_id, enquiry_no_raw=enquiry or "-", enquiry_no=enquiry, location_code_raw=location or "-", location_code=location, message=None, action_code_raw=action, action_code=action, source_raw="TEST", source="TEST", created_date=created)


async def seed_fast_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSessionFactory() as session:
        session.add_all([
            Location(location_id=1, location_group=1, booking_hub=None, cluster_id=None, location_code="L1", location_name="Test Central", location_dms=None, outlet_type_raw="SHOWROOM", outlet_type="SHOWROOM", outlet_function_raw=None, outlet_function=None, location_status=1, location_added_datetime=datetime(2026, 1, 1), latlng=None, latitude=None, longitude=None),
            Location(location_id=2, location_group=1, booking_hub=None, cluster_id=None, location_code="L2", location_name="Test East", location_dms=None, outlet_type_raw="E-OUTLET", outlet_type="E-OUTLET", outlet_function_raw=None, outlet_function=None, location_status=1, location_added_datetime=datetime(2026, 1, 1), latlng=None, latitude=None, longitude=None),
            _employee("sales-1", "Sana Sales", "SALES", "L1"), _employee("sales-2", "Sam Sales", "SALES", "L2"), _employee("finance-1", "Fina Finance", "FINANCE", "L1"), _employee("accounts-1", "Ari Accounts", "ACCOUNTS", "L1"), _employee("care-1", "Cora Care", "CUSTOMER CARE", "L1"), _employee("pdi-1", "Pia PDI", "PDI", "L1"),
            _employee("admin-1", "Ada Admin", "SALES", "L1", "ADMIN"),
        ])
        session.add_all([
            _event(1, "sales-1", "SALES", "BOOKING_CREATED", datetime(2026, 6, 28, 10), "B1", "L1"),
            _event(2, "finance-1", "FINANCE", "CREDIT_APPROVED", datetime(2026, 6, 28, 11), "B1", "L1"),
            _event(3, "accounts-1", "ACCOUNTS", "INVOICE_APPROVED_EDP", datetime(2026, 6, 29, 10), "B1", "L1"),
            _event(4, "care-1", "CUSTOMER CARE", "INSURANCE_APPROVED_BY_CCM", datetime(2026, 6, 29, 11), "B1", "L1"),
            _event(5, "pdi-1", "PDI", "PDI_INFO_ADDED", datetime(2026, 6, 30, 9), "B1", "L1"),
            _event(6, "pdi-1", "PDI", "DISPATCH_BY_PDI", datetime(2026, 6, 30, 10), "B1", "L1"),
            _event(7, "sales-1", "SALES", "DSE_COMMITMENTS_UPDATED", datetime(2026, 6, 30, 11), "B1", "L1", "DELIVERED"),
            _event(8, "sales-1", "SALES", "BOOKING_CREATED", datetime(2026, 6, 29, 9), "B2", "L1"),
            _event(9, "finance-1", "FINANCE", "CREDIT_APPROVED", datetime(2026, 6, 30, 12), "B2", "L1"),
            _event(10, "sales-2", "SALES", "BOOKING_CREATED", datetime(2026, 6, 29, 9), "B3", "L2"),
            _event(11, "sales-2", "SALES", "DSE_COMMITMENTS_UPDATED", datetime(2026, 6, 30, 13), "B3", "L2", "DELIVERED"),
            _event(12, "sales-1", "SALES", "BOOKING_CREATED", datetime(2026, 6, 30, 14), "B4", "L1"),
            _event(13, "sales-1", "SALES", "BOOKING_CREATED", datetime(2026, 6, 30, 15), "B5", "L1"),
            _event(14, "sales-1", "SALES", "DSE_COMMITMENTS_UPDATED", datetime(2026, 6, 30, 16), "B5", "L1", "DELIVERED"),
        ])
        await session.commit()
        await score_all_events(session)
        await materialize_gamification(session)
        await seed_quest_templates(session)
        await materialize_boss_battles(session)
