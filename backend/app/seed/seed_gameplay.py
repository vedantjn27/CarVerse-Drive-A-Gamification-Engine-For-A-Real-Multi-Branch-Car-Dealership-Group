"""Inspectable static Phase 4 game definitions; progress always comes from the XP ledger."""

QUEST_TEMPLATES = (
    {"code": "SALES_SHIFT_LAUNCH", "title": "Sales Shift Launch", "description": "Move one verified Sales booking milestone to start your demo drive.", "department": "SALES", "canonical_event": "VEHICLE_DELIVERED", "target_count": 1, "reward_xp": 20, "period": "WEEK", "sort_order": 0},
    {"code": "FINANCE_SHIFT_LAUNCH", "title": "Finance Shift Launch", "description": "Complete one verified finance approval and claim your launch reward.", "department": "FINANCE", "canonical_event": "FINANCE_APPROVED", "target_count": 1, "reward_xp": 20, "period": "WEEK", "sort_order": 0},
    {"code": "ACCOUNTS_SHIFT_LAUNCH", "title": "Accounts Shift Launch", "description": "Clear one verified invoice approval and claim your launch reward.", "department": "ACCOUNTS", "canonical_event": "INVOICE_APPROVED", "target_count": 1, "reward_xp": 20, "period": "WEEK", "sort_order": 0},
    {"code": "CARE_SHIFT_LAUNCH", "title": "Care Shift Launch", "description": "Secure one verified insurance approval and claim your launch reward.", "department": "CUSTOMER CARE", "canonical_event": "INSURANCE_APPROVED", "target_count": 1, "reward_xp": 20, "period": "WEEK", "sort_order": 0},
    {"code": "RTO_SHIFT_LAUNCH", "title": "RTO Shift Launch", "description": "Complete one verified registration milestone and claim your launch reward.", "department": "RTO / REGN TEAM", "canonical_event": "RTO_REGISTRATION_COMPLETED", "target_count": 1, "reward_xp": 20, "period": "WEEK", "sort_order": 0},
    {"code": "PDI_SHIFT_LAUNCH", "title": "PDI Shift Launch", "description": "Complete one verified PDI milestone and claim your launch reward.", "department": "PDI", "canonical_event": "PDI_COMPLETED", "target_count": 1, "reward_xp": 20, "period": "WEEK", "sort_order": 0},
    {"code": "OPERATIONS_SHIFT_LAUNCH", "title": "Operations Shift Launch", "description": "Complete one verified department handoff and claim your launch reward.", "department": None, "canonical_event": "OPERATIONAL_HANDOFF_COMPLETED", "target_count": 1, "reward_xp": 20, "period": "WEEK", "sort_order": 0},
    {"code": "DOCUMENTS_SPRINT", "title": "Paperwork Pace", "description": "Complete three verified document sets this week.", "department": "SALES", "canonical_event": "DOCUMENT_SET_COMPLETED", "target_count": 3, "reward_xp": 30, "period": "WEEK", "sort_order": 1},
    {"code": "HANDOFF_HELPER", "title": "Handoff Hero", "description": "Make two verified cross-department assists this week.", "department": None, "canonical_event": "CROSS_DEPT_ASSIST", "target_count": 2, "reward_xp": 25, "period": "WEEK", "sort_order": 2},
    {"code": "CLEAN_FINISHER", "title": "Clean Finisher", "description": "Contribute to two clean booking completions this week.", "department": None, "canonical_event": "CLEAN_BOOKING_BONUS", "target_count": 2, "reward_xp": 35, "period": "WEEK", "sort_order": 3},
    {"code": "DELIVERY_DRIVE", "title": "Delivery Drive", "description": "Deliver two vehicles this week.", "department": "SALES", "canonical_event": "VEHICLE_DELIVERED", "target_count": 2, "reward_xp": 40, "period": "WEEK", "sort_order": 4},
    {"code": "OPS_RELAY", "title": "Operations Relay", "description": "Complete two verified operational handoffs this week.", "department": None, "canonical_event": "OPERATIONAL_HANDOFF_COMPLETED", "target_count": 2, "reward_xp": 25, "period": "WEEK", "sort_order": 5},
)

BOSS_BATTLE_TEMPLATES = (
    ("SALES", "VEHICLE_DELIVERED", 15, "Delivery Dragon", "Deliver 15 vehicles as a team."),
    ("FINANCE", "FINANCE_APPROVED", 20, "Approval Avalanche", "Land 20 finance approvals as a team."),
    ("ACCOUNTS", "INVOICE_APPROVED", 20, "Invoice Ironclad", "Clear 20 invoice approvals as a team."),
    ("CUSTOMER CARE", "INSURANCE_APPROVED", 15, "Care Commander", "Secure 15 insurance approvals as a team."),
    ("PDI", "PDI_COMPLETED", 18, "PDI Pit Crew", "Complete 18 PDI milestones as a team."),
    ("EDP", "OPERATIONAL_HANDOFF_COMPLETED", 12, "Backend Blitz", "Complete 12 verified operational handoffs as a team."),
    ("ACCESSORIES", "OPERATIONAL_HANDOFF_COMPLETED", 10, "Fitment Force", "Complete 10 verified accessory handoffs as a team."),
    ("TRUEVALUE", "OPERATIONAL_HANDOFF_COMPLETED", 10, "Value Vault", "Complete 10 verified exchange handoffs as a team."),
    ("SECURITY", "OPERATIONAL_HANDOFF_COMPLETED", 8, "Clearance Crew", "Complete 8 verified clearance handoffs as a team."),
    ("SERVICE", "OPERATIONAL_HANDOFF_COMPLETED", 10, "Service Sprint", "Complete 10 verified service handoffs as a team."),
    ("TRANSPORT", "OPERATIONAL_HANDOFF_COMPLETED", 8, "Transit Team", "Complete 8 verified transport handoffs as a team."),
)
