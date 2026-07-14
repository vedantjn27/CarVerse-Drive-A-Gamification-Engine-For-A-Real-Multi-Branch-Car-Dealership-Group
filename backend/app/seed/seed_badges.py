"""Data definitions for level titles and achievement badges."""

LEVEL_TITLES = (
    {"code": "ROOKIE_CLOSER", "display_name": "Rookie Closer", "minimum_level": 1, "description": "The first step onto the CarVerse track."},
    {"code": "DEAL_NAVIGATOR", "display_name": "Deal Navigator", "minimum_level": 3, "description": "Consistently moves bookings through real milestones."},
    {"code": "MOMENTUM_MAKER", "display_name": "Momentum Maker", "minimum_level": 6, "description": "Builds reliable delivery momentum."},
    {"code": "TEAM_CATALYST", "display_name": "Team Catalyst", "minimum_level": 10, "description": "Creates results across departmental boundaries."},
    {"code": "DEAL_WHISPERER", "display_name": "Deal Whisperer", "minimum_level": 15, "description": "Turns difficult workflows into clean outcomes."},
    {"code": "DELIVERY_LEGEND", "display_name": "Delivery Legend", "minimum_level": 20, "description": "A top-tier CarVerse performer."},
)

BADGES = (
    {"code": "FIRST_VERIFIED_MOVE", "name": "First Verified Move", "description": "Move any verified dealership milestone for the first time.", "icon": "flag", "criteria_type": "ANY_MILESTONE", "canonical_event": None, "threshold": 1, "sort_order": 0},
    {"code": "LEVEL_UP", "name": "Momentum Level-Up", "description": "Reach level two through verified performance.", "icon": "medal", "criteria_type": "MIN_LEVEL", "canonical_event": None, "threshold": 2, "sort_order": 1},
    {"code": "BOSS_VICTOR", "name": "Boss Victor", "description": "Claim a completed department boss reward.", "icon": "trophy", "criteria_type": "BOSS_CLAIM", "canonical_event": None, "threshold": 1, "sort_order": 2},
    {"code": "FINANCE_ACE", "name": "Finance Ace", "description": "Complete a verified finance approval.", "icon": "trophy", "criteria_type": "EVENT_COUNT", "canonical_event": "FINANCE_APPROVED", "threshold": 1, "sort_order": 1},
    {"code": "INVOICE_ACE", "name": "Invoice Ace", "description": "Complete a verified invoice approval.", "icon": "trophy", "criteria_type": "EVENT_COUNT", "canonical_event": "INVOICE_APPROVED", "threshold": 1, "sort_order": 2},
    {"code": "CARE_ACE", "name": "Care Ace", "description": "Complete a verified insurance approval.", "icon": "trophy", "criteria_type": "EVENT_COUNT", "canonical_event": "INSURANCE_APPROVED", "threshold": 1, "sort_order": 3},
    {"code": "RTO_ACE", "name": "Registration Ace", "description": "Complete a verified registration milestone.", "icon": "trophy", "criteria_type": "EVENT_COUNT", "canonical_event": "RTO_REGISTRATION_COMPLETED", "threshold": 1, "sort_order": 4},
    {"code": "PDI_ACE", "name": "PDI Ace", "description": "Complete a verified PDI milestone.", "icon": "trophy", "criteria_type": "EVENT_COUNT", "canonical_event": "PDI_COMPLETED", "threshold": 1, "sort_order": 5},
    {"code": "OPS_ACE", "name": "Operations Ace", "description": "Complete a verified operational handoff.", "icon": "trophy", "criteria_type": "EVENT_COUNT", "canonical_event": "OPERATIONAL_HANDOFF_COMPLETED", "threshold": 1, "sort_order": 6},
    {"code": "FIRST_DELIVERY", "name": "First Delivery", "description": "Complete the first vehicle delivery.", "icon": "flag", "criteria_type": "EVENT_COUNT", "canonical_event": "VEHICLE_DELIVERED", "threshold": 1, "sort_order": 1},
    {"code": "SPEED_CLOSER", "name": "Speed Closer", "description": "Earn five fast-delivery bonuses.", "icon": "speedometer", "criteria_type": "EVENT_COUNT", "canonical_event": "FAST_DELIVERY_BONUS", "threshold": 5, "sort_order": 2},
    {"code": "CLEAN_SWEEP", "name": "Clean Sweep", "description": "Contribute to ten clean bookings.", "icon": "sparkles", "criteria_type": "EVENT_COUNT", "canonical_event": "CLEAN_BOOKING_BONUS", "threshold": 10, "sort_order": 3},
    {"code": "FIREFIGHTER", "name": "Firefighter", "description": "Resolve ten escalations within the recovery window.", "icon": "fire-extinguisher", "criteria_type": "EVENT_COUNT", "canonical_event": "ESCALATION_RESOLVED", "threshold": 10, "sort_order": 4},
    {"code": "COMEBACK_KID", "name": "Comeback Kid", "description": "Save five cancellation requests and deliver the vehicles.", "icon": "rotate-ccw", "criteria_type": "EVENT_COUNT", "canonical_event": "CANCELLATION_SAVE", "threshold": 5, "sort_order": 5},
    {"code": "TEAM_PLAYER", "name": "Team Player", "description": "Earn twenty cross-department assists.", "icon": "users", "criteria_type": "EVENT_COUNT", "canonical_event": "CROSS_DEPT_ASSIST", "threshold": 20, "sort_order": 6},
    {"code": "IRON_STREAK", "name": "Iron Streak", "description": "Maintain a thirty-day real-milestone streak.", "icon": "flame", "criteria_type": "LONGEST_STREAK", "canonical_event": None, "threshold": 30, "sort_order": 7},
    {"code": "BRANCH_CHAMPION", "name": "Branch Champion", "description": "Finish in the highest normalized monthly branch position.", "icon": "trophy", "criteria_type": "BRANCH_CHAMPION", "canonical_event": None, "threshold": 1, "sort_order": 8},
)
