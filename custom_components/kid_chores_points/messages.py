"""Notification / logbook texts, in the Home Assistant system language."""

from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "mandatory_done_title": "Today's chores done! ⭐",
        "mandatory_done": "Great job! The bonus chores are unlocked.",
        "pending_released": " Your {n} waiting bonus points were added.",
        "pending_title": "Bonus points saved ⏳",
        "pending": 'Your {pts} points for "{task}" are added once today\'s chores are done. Left: {left}',
        "not_enough_title": "Not enough points",
        "not_enough": "{label} costs {cost} points, you have {bank}.",
        "redeemed_note": "Redeemed {when} for {cost} points",
        "redeemed_log": "redeemed {label} for {cost} points ({left} left)",
        "redeemed_parents_title": "Reward redeemed 🎁",
        "redeemed_parents": "{label} ({cost} p). {left} points left in the bank.",
        "redeemed_kid_title": "Redeemed! 🎉",
        "redeemed_kid": "{label} – tell a parent. {left} points left.",
        "adjust_log": "adjusted {target} by {points} ({reason})",
        "no_reason": "no reason given",
        "week": "week",
        "bank": "bank",
        "last_week": "{week}/{goal} {mark} · +{to_bank} to the bank",
        "week_log": "week closed: {week}/{goal} points, {to_bank} to the bank",
        "week_met_title": "Weekly goal reached! 🏆",
        "week_over_title": "The week is over",
        "week_kid": "You got {week} of {goal} points. {to_bank} points were added to the bank ({bank} total).",
        "week_parents_title": "Weekly summary",
        "week_parents": "{week}/{goal} points ({result}). +{to_bank} to the bank, balance {bank}.",
        "goal_met": "goal met",
        "goal_missed": "goal missed",
    },
    "sv": {
        "mandatory_done_title": "Dagens uppgifter klara! ⭐",
        "mandatory_done": "Bra jobbat! Bonusuppgifterna är upplåsta.",
        "pending_released": " Dina {n} väntande bonuspoäng är nu insatta.",
        "pending_title": "Bonuspoäng sparade ⏳",
        "pending": 'Dina {pts} poäng för "{task}" sätts in när dagens uppgifter är klara. Kvar: {left}',
        "not_enough_title": "Inte tillräckligt med poäng",
        "not_enough": "{label} kostar {cost} poäng, du har {bank}.",
        "redeemed_note": "Inlöst {when} för {cost} poäng",
        "redeemed_log": "löste in {label} för {cost} poäng ({left} kvar)",
        "redeemed_parents_title": "Belöning inlöst 🎁",
        "redeemed_parents": "{label} ({cost} p). {left} poäng kvar i banken.",
        "redeemed_kid_title": "Inlöst! 🎉",
        "redeemed_kid": "{label} – säg till mamma eller pappa. {left} poäng kvar.",
        "adjust_log": "justerade {target} med {points} ({reason})",
        "no_reason": "ingen anledning angiven",
        "week": "veckan",
        "bank": "banken",
        "last_week": "{week}/{goal} {mark} · +{to_bank} till banken",
        "week_log": "veckan stängd: {week}/{goal} poäng, {to_bank} till banken",
        "week_met_title": "Veckomålet klarat! 🏆",
        "week_over_title": "Veckan är slut",
        "week_kid": "Du fick {week} av {goal} poäng. {to_bank} poäng har satts in i banken ({bank} totalt).",
        "week_parents_title": "Veckosammanfattning",
        "week_parents": "{week}/{goal} poäng ({result}). +{to_bank} till banken, saldo {bank}.",
        "goal_met": "mål nått",
        "goal_missed": "mål ej nått",
    },
}


def translate(language: str, key: str, **kwargs: object) -> str:
    """Return the text for `key` in `language` (falls back to English)."""
    table = MESSAGES.get(language.split("-")[0].lower(), MESSAGES["en"])
    return table.get(key, MESSAGES["en"][key]).format(**kwargs)
