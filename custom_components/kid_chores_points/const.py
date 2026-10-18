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
CONF_REWARDS = "rewards"  # {reward label (per unit): points cost per unit}
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
    CONF_REWARDS: {},
    CONF_KID_PERSONS: [],
    CONF_PARENT_PERSONS: [],
    CONF_NOTIFY_KID: [],
    CONF_NOTIFY_PARENTS: [],
}

SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"

# Service names / fields
SERVICE_COMPLETE = "complete_chore"
SERVICE_REDEEM = "redeem"
SERVICE_ADJUST = "adjust_points"
SERVICE_CLOSE_WEEK = "close_week"
ATTR_ENTRY = "config_entry"
