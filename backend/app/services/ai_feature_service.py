"""AI-flavoured views derived from deterministic dealership facts."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AnomalyReview, BossBattle, Employee, LocationStats, UserStats, XPLedger
from app.services.ai_provider import ai_provider
from app.services.boss_battle_service import boss_battle
from app.services.quest_service import quest_board


async def nudge_for_user(session: AsyncSession, user_id: str) -> dict[str, str]:
    stats = await session.get(UserStats, user_id)
    employee = await session.get(Employee, user_id)
    if stats is None or employee is None:
        raise ValueError("Employee stats are unavailable")
    remaining = max(stats.next_level_xp - stats.current_level_xp, 0)
    fallback = f"{employee.name or 'Teammate'}, you are {remaining} XP from your next level. Keep your next real booking milestone moving."
    return await ai_provider.generate(session, feature="nudge", system_prompt="You are a concise, encouraging dealership game coach. Never invent metrics or award points.", user_prompt=f"Employee department: {employee.department}. Total XP: {stats.total_xp}. Current streak: {stats.current_streak}. XP remaining in level: {remaining}. Write one sentence.", fallback=fallback)


async def recap_for_target(session: AsyncSession, target: str) -> dict[str, str]:
    normalized = target.strip().upper()
    department_total = await session.scalar(select(func.sum(XPLedger.leaderboard_points)).where(XPLedger.department == normalized))
    if department_total is not None:
        context = f"Department {normalized} has {department_total} competitive XP in the supplied event period."
    else:
        branch = await session.get(LocationStats, target.strip().upper())
        if branch is None:
            raise ValueError("No department or branch matches this target")
        context = f"Branch {branch.location_code} has {branch.leaderboard_xp} competitive XP across {branch.booking_attempts} booking attempts."
    fallback = f"{context} The team can build on verified milestones and clean handoffs in the next period."
    return await ai_provider.generate(session, feature="recap", system_prompt="Write a factual 2-sentence dealership weekly recap. Never fabricate names, metrics, or results.", user_prompt=context, fallback=fallback)


async def quest_flavour(session: AsyncSession, user_id: str) -> dict[str, object]:
    board = await quest_board(session, user_id)
    candidates = sorted(
        board["quests"],
        key=lambda item: (
            item["claimed"],
            item["completed"],
            item["target_count"] - item["progress"],
            item["code"],
        ),
    )[:3]
    dynamic_quests = [
        {
            "code": item["code"],
            "canonical_event": item["canonical_event"],
            "progress": item["progress"],
            "target_count": item["target_count"],
            "remaining": max(item["target_count"] - item["progress"], 0),
            "completion_criteria": f"Earn {item['target_count']} {item['canonical_event']} awards in the current event-data week.",
            "reward_xp": item["reward_xp"],
        }
        for item in candidates
    ]
    fallback = "Choose the nearest verified milestone target and let clean, cross-team work carry you there."
    result = await ai_provider.generate(session, feature="quest_flavour", system_prompt="Write one short motivating headline for these deterministic quest suggestions. Do not change targets, rewards, canonical events, or completion rules.", user_prompt=f"Quest suggestions: {dynamic_quests}", fallback=fallback)
    return {"board": board, "dynamic_quests": dynamic_quests, "flavour": result}


async def boss_flavour(session: AsyncSession, battle_id: str) -> dict[str, object] | None:
    battle = await boss_battle(session, battle_id)
    if battle is None:
        return None
    fallback = f"{battle['title']}: {battle['remaining']} verified {battle['canonical_event']} milestones remain before the team clears this challenge."
    result = await ai_provider.generate(session, feature="boss_flavour", system_prompt="Write one concise, energetic boss-battle flavour line. Do not alter the target or progress.", user_prompt=f"Battle facts: {battle}", fallback=fallback)
    return {"battle": battle, "flavour": result}


async def anomaly_explanation(session: AsyncSession, review_id: int) -> dict[str, str] | None:
    review = await session.get(AnomalyReview, review_id)
    if review is None:
        return None
    fallback = f"This review is flagged because the employee's {review.metric} was {review.z_score:.2f} standard deviations from the {review.department or 'overall'} cohort mean. It is a review signal, not a penalty."
    return await ai_provider.generate(session, feature="anomaly_explanation", system_prompt="Explain a statistical review flag in plain, neutral language. It is not evidence of wrongdoing and must not recommend punishment.", user_prompt=f"Metric={review.metric}; value={review.metric_value}; mean={review.cohort_mean}; stddev={review.cohort_stddev}; z={review.z_score}; department={review.department}", fallback=fallback)
