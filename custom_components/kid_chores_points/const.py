"""Constants for Kid Chores & Points."""

DOMAIN = "kid_chores_points"
CARD_URL = "/kid_chores_points/kid-chores-cards.js"
PLATFORMS = ["sensor", "binary_sensor", "todo"]

# Fired by Maintenance Supporter (iluebbe/maintenance_supporter)
MS_DOMAIN = "maintenance_supporter"
MS_DUE_STATES = ("overdue", "triggered", "due_soon")  # the task sensor states that mean "do it now"
EVENT_TASK_COMPLETED = "maintenance_supporter_task_completed"

# Option keys
CONF_GOAL = "weekly_goal"
CONF_GOAL_BONUS = "goal_bonus"
CONF_POLICY = "missed_goal_policy"
CONF_WEEK_START = "week_start"
CONF_MANDATORY = "mandatory"  # {task name: points}
CONF_BONUS = "bonus"  # {task name: points}
CONF_CHORE_IDS = "chore_ids"  # {chore name: Maintenance Supporter task id}
CONF_REWARDS = "rewards"  # {reward label (per unit): points cost per unit}
CONF_REWARD_PAYOUT = "reward_payout"  # {reward label: wallet money per unit}
CONF_HISTORY_LIMIT = "history_limit"  # how many history entries are kept
CONF_WEEK_BREAKDOWN = "week_breakdown"  # per-chore counts in the parents' weekly summary
CONF_BEDTIME = "bedtime"  # "HH:MM", empty = no reminder
CONF_BEDTIME_WEEKEND = "bedtime_weekend"  # "HH:MM" for Friday and Saturday nights, empty = same
CONF_BEDTIME_LEAD = "bedtime_lead"  # minutes before bedtime to send the reminder
CONF_MEDALS = "medals_enabled"  # streaks and medals on/off
CONF_MEDALS_GRACE = "medals_grace"  # forgive one missed day per week in a day streak
CONF_MEDALS_NOTIFY = "medals_notify"  # notify when a medal is earned
CONF_MEDAL_RULES = "medal_rules"  # {medal id: {"at": n, "bonus": points}}, overrides of the catalogue
CONF_LANGUAGE_KID = "language_kid"  # notification language for the child: "auto" or a language code
CONF_LANGUAGE_PARENTS = "language_parents"  # same, for the parents
CONF_CURRENCY = "currency"  # wallet currency label, e.g. "kr"
CONF_NOTIFY_KID = "notify_kid"  # extra notify service names for the child
CONF_NOTIFY_PARENTS = "notify_parents"  # extra notify service names for parents
CONF_KID_PERSONS = "kid_persons"  # person entity ids
CONF_PARENT_PERSONS = "parent_persons"  # person entity ids

LANGUAGE_AUTO = "auto"  # the language of the person's Home Assistant profile, else the system language

WEEKEND_NIGHTS = (4, 5)  # weekday() of Friday and Saturday: no school the next day

WEEK_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]  # index = weekday()

POLICY_ANYWAY = "bank_anyway"
POLICY_HALF = "bank_half"
POLICY_FORFEIT = "forfeit"
POLICIES = [POLICY_ANYWAY, POLICY_HALF, POLICY_FORFEIT]

DEFAULT_OPTIONS = {
    CONF_GOAL: 50,
    CONF_GOAL_BONUS: 0,
    CONF_POLICY: POLICY_ANYWAY,
    CONF_WEEK_START: "mon",
    CONF_MANDATORY: {},
    CONF_BONUS: {},
    CONF_CHORE_IDS: {},
    CONF_REWARDS: {},
    CONF_REWARD_PAYOUT: {},
    CONF_LANGUAGE_KID: "auto",
    CONF_LANGUAGE_PARENTS: "auto",
    CONF_MEDALS: False,
    CONF_MEDALS_GRACE: False,
    CONF_MEDALS_NOTIFY: True,
    CONF_MEDAL_RULES: {},
    CONF_CURRENCY: "kr",
    CONF_HISTORY_LIMIT: 300,
    CONF_WEEK_BREAKDOWN: True,
    CONF_BEDTIME: "",
    CONF_BEDTIME_WEEKEND: "",
    CONF_BEDTIME_LEAD: 45,
    CONF_KID_PERSONS: [],
    CONF_PARENT_PERSONS: [],
    CONF_NOTIFY_KID: [],
    CONF_NOTIFY_PARENTS: [],
}

HISTORY_LIMIT = 300  # default number of entries kept in the points history
HISTORY_LIMIT_MIN = 50
HISTORY_LIMIT_MAX = 1000  # the whole history is an attribute of one sensor

MEDAL_BONUS_MAX = 50  # most bonus points one medal can pay
PERFECT_DAYS_KEPT = 400  # days of streak history kept (a day-streak medal can't need more)

SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"

# Service names / fields
SERVICE_COMPLETE = "complete_chore"
SERVICE_REDEEM = "redeem"
SERVICE_ADJUST = "adjust_points"
SERVICE_ADJUST_WALLET = "adjust_wallet"
SERVICE_CLOSE_WEEK = "close_week"
SERVICE_UNDO = "undo"
SERVICE_REVERT = "revert"
ATTR_ENTRY = "config_entry"
