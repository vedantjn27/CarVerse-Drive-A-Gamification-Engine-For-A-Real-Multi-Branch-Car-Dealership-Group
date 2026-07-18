export interface HealthResponse { status: 'ok'; service: string; environment: string; database: 'connected'; timestamp: string; process_started_at: string; }
export interface LoginResponse { access_token: string; token_type: 'bearer'; expires_in_seconds: number; employee_id: string; role: 'AGENT' | 'MANAGER' | 'ADMIN'; }
export interface Badge { code: string; name: string; description: string; icon: string; awarded_at: string; evidence: Record<string, unknown>; }
export interface Profile {
  employee_id: string; name: string | null; designation: string | null; department: string | null; location_code: string | null; role: string | null;
  total_xp: number; leaderboard_xp: number; streak_bonus_xp: number; level: number; title: string; current_level_xp: number; next_level_xp: number;
  current_streak: number; longest_streak: number; reputation: number; total_awards: number; milestone_awards: number; deliveries: number;
  clean_bookings: number; fast_deliveries: number; escalations_resolved: number; cancellation_saves: number; cross_dept_assists: number;
  rework_discounted_awards: number; all_time_rank: number | null; department_rank: number | null; location_rank: number | null; last_earned_at: string | null; badges: Badge[];
}
export interface Leaderboard { scope: string; anchor_at: string | null; starts_at: string | null; dealership_score: number; entries: Array<Record<string, unknown>>; }
export interface BossBattle { id: string; department: string; canonical_event: string; title: string; description: string; starts_at: string; ends_at: string; progress: number; target_count: number; completed: boolean; reward_pool_xp: number; contributors: number; remaining: number; eligible_to_claim: boolean; claimed: boolean; }
export interface Quest { code: string; title: string; description: string; canonical_event: string; progress: number; target_count: number; reward_xp: number; completed: boolean; claimed: boolean; }
export interface QuestBoard { anchor_at: string | null; starts_at: string | null; ends_at: string | null; quests: Quest[]; }
export interface AiText { text: string; provider: string; cached: string; }
export interface DynamicQuest { code: string; canonical_event: string; progress: number; target_count: number; remaining: number; completion_criteria: string; reward_xp: number; }
export interface AiQuestBoard { board: QuestBoard; dynamic_quests: DynamicQuest[]; flavour: AiText; }
export interface ActiveBooking { location_code: string; enquiry_no: string; status: string; current_stage: string; progress_percent: number; last_event_at: string; departments_touched: string[]; }
export interface RaceStage { stage: string; label: string; responsible_department: string; order: number; reached: boolean; current: boolean; }
export interface BookingRace { location_code: string; enquiry_no: string; status: string; current_stage: string; progress_percent: number; sales_owner_user_id: string | null; sales_owner_name: string | null; total_events: number; milestone_count: number; escalation_count: number; first_event_at: string; last_event_at: string; booking_created_at: string | null; delivered_at: string | null; departments_touched: string[]; track: RaceStage[]; milestones: Array<{ canonical_event: string; earned_at: string; department: string; user_id: string; points: number }>; }
export interface Anomaly { id: number; user_id: string; department: string; metric: string; metric_value: number; cohort_mean: number; cohort_stddev: number; z_score: number; threshold: number; explanation: string; status: string; detected_at: string; resolution_note: string | null; }
