"""Constants for Kid Chores & Points."""

DOMAIN = "kid_chores_points"
CARD_URL = "/kid_chores_points/kid-chores-cards.js"
PLATFORMS = ["sensor", "binary_sensor", "todo"]

# Fired by Maintenance Supporter (iluebbe/maintenance_supporter)
MS_DOMAIN = "maintenance_supporter"
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
CONF_CURRENCY = "currency"  # wallet currency label, e.g. "kr"
CONF_NOTIFY_KID = "notify_kid"  # extra notify service names for the child
CONF_NOTIFY_PARENTS = "notify_parents"  # extra notify service names for parents
CONF_KID_PERSONS = "kid_persons"  # person entity ids
CONF_PARENT_PERSONS = "parent_persons"  # person entity ids

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
    CONF_CURRENCY: "kr",
    CONF_HISTORY_LIMIT: 300,
    CONF_KID_PERSONS: [],
    CONF_PARENT_PERSONS: [],
    CONF_NOTIFY_KID: [],
    CONF_NOTIFY_PARENTS: [],
}

HISTORY_LIMIT = 300  # default number of entries kept in the points history
HISTORY_LIMIT_MIN = 50
HISTORY_LIMIT_MAX = 1000  # the whole history is an attribute of one sensor
UNDO_LIMIT = 10  # how many changes can be undone, one after another

SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"

# Service names / fields
SERVICE_COMPLETE = "complete_chore"
SERVICE_REDEEM = "redeem"
SERVICE_ADJUST = "adjust_points"
SERVICE_ADJUST_WALLET = "adjust_wallet"
SERVICE_CLOSE_WEEK = "close_week"
SERVICE_UNDO = "undo"
ATTR_ENTRY = "config_entry"
