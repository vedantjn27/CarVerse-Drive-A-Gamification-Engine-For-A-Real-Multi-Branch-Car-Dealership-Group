"""Human-reviewable z-score anomaly detection; never changes rewards or ranks."""

from collections import defaultdict
from datetime import UTC, datetime
from math import sqrt

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import AnomalyReview, UserStats, XPLedger


async def scan_anomalies(session: AsyncSession) -> int:
    booking_counts: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in (await session.execute(select(XPLedger.user_id, XPLedger.location_code, XPLedger.enquiry_no))).all():
        if row.location_code and row.enquiry_no:
            booking_counts[row.user_id].add((row.location_code, row.enquiry_no))
    stats = list((await session.execute(select(UserStats))).scalars())
    groups: dict[str, list[tuple[UserStats, float]]] = defaultdict(list)
    for item in stats:
        touched = len(booking_counts[item.user_id])
        if touched:
            groups[item.department or "UNASSIGNED"].append((item, item.leaderboard_xp / touched))
    now = datetime.now(UTC).replace(tzinfo=None)
    rows = []
    for department, values in groups.items():
        if len(values) < 3:
            continue
        mean = sum(value for _, value in values) / len(values)
        variance = sum((value - mean) ** 2 for _, value in values) / len(values)
        stddev = sqrt(variance)
        if stddev == 0:
            continue
        for item, value in values:
            z_score = (value - mean) / stddev
            if abs(z_score) >= settings.anomaly_z_threshold:
                rows.append(AnomalyReview(user_id=item.user_id, department=department, metric="leaderboard_xp_per_booking", metric_value=value, cohort_mean=mean, cohort_stddev=stddev, z_score=z_score, threshold=settings.anomaly_z_threshold, explanation="Automated statistical review flag; no points or rank were changed.", status="OPEN", detected_at=now, resolved_at=None, resolved_by_user_id=None, resolution_note=None))
    await session.execute(delete(AnomalyReview).where(AnomalyReview.status == "OPEN"))
    session.add_all(rows)
    await session.commit()
    return len(rows)
