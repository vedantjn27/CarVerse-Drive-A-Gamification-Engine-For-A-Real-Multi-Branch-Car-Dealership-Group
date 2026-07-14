"""The complete, inspectable set of canonical CarVerse scoring rules."""

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class CanonicalEvent(StrEnum):
    BOOKING_CREATED = "BOOKING_CREATED"
    DOCUMENT_SET_COMPLETED = "DOCUMENT_SET_COMPLETED"
    DISCOUNT_APPROVED = "DISCOUNT_APPROVED"
    FINANCE_APPROVED = "FINANCE_APPROVED"
    INVOICE_APPROVED = "INVOICE_APPROVED"
    GATEPASS_ISSUED = "GATEPASS_ISSUED"
    INSURANCE_APPROVED = "INSURANCE_APPROVED"
    RTO_REGISTRATION_COMPLETED = "RTO_REGISTRATION_COMPLETED"
    PDI_COMPLETED = "PDI_COMPLETED"
    DISPATCHED = "DISPATCHED"
    VEHICLE_DELIVERED = "VEHICLE_DELIVERED"
    FAST_DELIVERY_BONUS = "FAST_DELIVERY_BONUS"
    CLEAN_BOOKING_BONUS = "CLEAN_BOOKING_BONUS"
    CROSS_DEPT_ASSIST = "CROSS_DEPT_ASSIST"
    ESCALATION_RESOLVED = "ESCALATION_RESOLVED"
    CANCELLATION_SAVE = "CANCELLATION_SAVE"
    DAILY_LOGIN_STREAK = "DAILY_LOGIN_STREAK"
    FOLLOW_UP_LOGGED = "FOLLOW_UP_LOGGED"
    OPERATIONAL_HANDOFF_COMPLETED = "OPERATIONAL_HANDOFF_COMPLETED"


class RuleType(StrEnum):
    MILESTONE = "MILESTONE"
    OUTCOME = "OUTCOME"
    OUTCOME_BONUS = "OUTCOME_BONUS"
    COLLABORATION = "COLLABORATION"
    GUARDED_REPEATABLE = "GUARDED_REPEATABLE"


@dataclass(frozen=True, slots=True)
class ScoringRule:
    event: CanonicalEvent
    display_name: str
    rule_type: RuleType
    base_xp: int
    owner_department: str
    raw_signals: tuple[str, ...]
    anti_gaming_rule: str


_RULES = (
    ScoringRule(CanonicalEvent.BOOKING_CREATED, "Booking Created", RuleType.MILESTONE, 20, "SALES", ("BOOKING_CREATED",), "once per booking"),
    ScoringRule(CanonicalEvent.DOCUMENT_SET_COMPLETED, "Document Set Completed", RuleType.MILESTONE, 25, "SALES/CUSTOMER CARE", ("DERIVED:REQUIRED_DOCUMENT_SET",), "once after all eight exact document slots"),
    ScoringRule(CanonicalEvent.DISCOUNT_APPROVED, "Discount Approved", RuleType.MILESTONE, 15, "SALES", ("DISCOUNT_APPROVED",), "once per booking"),
    ScoringRule(CanonicalEvent.FINANCE_APPROVED, "Finance Approved", RuleType.OUTCOME, 30, "FINANCE", ("CREDIT_APPROVED",), "once per booking; actual source actor retained"),
    ScoringRule(CanonicalEvent.INVOICE_APPROVED, "Invoice Approved", RuleType.MILESTONE, 25, "ACCOUNTS", ("INVOICE_APPROVED_SALES", "INVOICE_APPROVED_EDP"), "first approval leg per booking"),
    ScoringRule(CanonicalEvent.GATEPASS_ISSUED, "Gatepass Issued", RuleType.MILESTONE, 15, "ACCOUNTS", ("GATEPASS_ISSUED_BY_ACCOUNTS",), "once per booking"),
    ScoringRule(CanonicalEvent.INSURANCE_APPROVED, "Insurance Approved", RuleType.OUTCOME, 20, "CUSTOMER CARE", ("INSURANCE_APPROVED_BY_CCM",), "once per booking"),
    ScoringRule(CanonicalEvent.RTO_REGISTRATION_COMPLETED, "RTO Registration Completed", RuleType.MILESTONE, 20, "RTO / REGN TEAM", ("REGISTRATION_APPROVED_SALES", "REGISTRATION_CREATED"), "first approved/created registration state"),
    ScoringRule(CanonicalEvent.PDI_COMPLETED, "PDI Completed", RuleType.MILESTONE, 25, "PDI", ("PDI_INFO_ADDED",), "once; PDI_INFO_UPDATED scores zero"),
    ScoringRule(CanonicalEvent.DISPATCHED, "Dispatched", RuleType.OUTCOME, 20, "PDI/CUSTOMER CARE", ("DISPATCH_BY_PDI", "DISPATCH_BY_CCM"), "first dispatch leg per booking"),
    ScoringRule(CanonicalEvent.VEHICLE_DELIVERED, "Vehicle Delivered", RuleType.OUTCOME, 100, "SALES", ("DERIVED:FIRST_DELIVERED_STAGE",), "once per booking"),
    ScoringRule(CanonicalEvent.FAST_DELIVERY_BONUS, "Fast Delivery Bonus", RuleType.OUTCOME_BONUS, 40, "BOOKING TEAM", ("DERIVED:BRANCH_ROLLING_MEDIAN",), "once at delivery with a prior branch benchmark"),
    ScoringRule(CanonicalEvent.CLEAN_BOOKING_BONUS, "Clean Booking Bonus", RuleType.OUTCOME_BONUS, 30, "BOOKING TEAM", ("DERIVED:CLEAN_DELIVERY",), "once at delivery"),
    ScoringRule(CanonicalEvent.CROSS_DEPT_ASSIST, "Cross-Department Assist", RuleType.COLLABORATION, 10, "COLLABORATING DEPARTMENTS", ("DERIVED:FAST_FORWARD_HANDOFF",), "different users/departments; capped per booking"),
    ScoringRule(CanonicalEvent.ESCALATION_RESOLVED, "Escalation Resolved", RuleType.COLLABORATION, 15, "RESOLVING DEPARTMENT", ("DERIVED:ESCALATION_THEN_RESOLUTION",), "one resolver per escalation; different user/department"),
    ScoringRule(CanonicalEvent.CANCELLATION_SAVE, "Cancellation Save", RuleType.OUTCOME, 25, "SALES/CUSTOMER CARE", ("DERIVED:CANCELLATION_REQUEST_THEN_DELIVERY",), "once per delivered booking without approval"),
    ScoringRule(CanonicalEvent.DAILY_LOGIN_STREAK, "Daily Login", RuleType.GUARDED_REPEATABLE, 2, "ALL", ("USER_LOGGED_IN",), "first login per user per calendar day"),
    ScoringRule(CanonicalEvent.FOLLOW_UP_LOGGED, "Follow-Up Logged", RuleType.GUARDED_REPEATABLE, 1, "SALES", ("BOOKING_NOTE_ADDED",), "maximum three per booking per day while active"),
    ScoringRule(CanonicalEvent.OPERATIONAL_HANDOFF_COMPLETED, "Operational Handoff Completed", RuleType.MILESTONE, 12, "OPERATIONS", ("DERIVED:ROLE_WORK_ORDER",), "once per employee, work item, and day; production source integration required"),
)

if len(_RULES) > 20:
    raise RuntimeError("The hackathon contract permits at most 20 scoring actions")
if len({rule.event for rule in _RULES}) != len(_RULES):
    raise RuntimeError("Canonical scoring event keys must be unique")

SCORING_RULES = MappingProxyType({rule.event: rule for rule in _RULES})

RAW_MILESTONE_SIGNALS = MappingProxyType({
    signal: rule.event
    for rule in _RULES
    for signal in rule.raw_signals
    if not signal.startswith("DERIVED:")
    and rule.event not in {CanonicalEvent.DAILY_LOGIN_STREAK, CanonicalEvent.FOLLOW_UP_LOGGED}
})

REQUIRED_DOCUMENT_ACTIONS = frozenset({
    "DOCUMENTS_AADHAAR FRONT", "DOCUMENTS_AADHAAR BACK", "DOCUMENTS_PAN",
    "DOCUMENTS_VIN", "DOCUMENTS_FRONT", "DOCUMENTS_REAR", "DOCUMENTS_LEFT", "DOCUMENTS_RIGHT",
})

ZERO_XP_ACTIONS = frozenset({
    "FINANCE_INFO_UPDATED", "FINANCE_STATUS_INFO_UPDATED", "PDI_INFO_UPDATED",
    "PAYMENTS_UPDATED", "PAYMENT_ADDED", "DISCOUNT_UPDATED", "DEBIT_ADDED",
})
