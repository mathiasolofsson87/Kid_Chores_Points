# Roadmap / ideas

Suggestions noted on 2026-10-20 (at v1.4.5). Tick items off as they are done.

Suggested order: 1 + 2, then 3, then 13, then 5 and 6.

## Reliability and quality

- [x] 1. **Tests.** (done: 47 tests in `tests/`; run with `.venv/bin/python -m pytest`, setup: `uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -r requirements_test.txt`) Add `tests/` with pytest and `pytest-homeassistant-custom-component`. Cover week close, bonus banking, the missed-goal policies (all / half / forfeit), wallet floor at 0 and pending bonus dropped at midnight.
- [x] 2. **CI.** (done: `.github/workflows/validate.yml`, needs a first run on GitHub to confirm) GitHub Actions with hassfest, HACS validation and pytest.
- [ ] 3. **Swedish config flow.** Add `translations/sv.json`; only `en.json` exists, so the config and options flow is English-only.
- [ ] 4. **Releases and changelog.** Tagged GitHub releases with short notes, so HACS users see what changed.

## Features

- [ ] 5. **Undo.** Revert a mistaken completion or redemption, e.g. a revert action on History card entries.
- [ ] 6. **Parent approval mode.** Optional: a "Done" tap goes to pending and a parent confirms it via an actionable notification.
- [ ] 7. **Streaks and badges.** E.g. 7 days in a row, or all chores every day of the week, with an optional point bonus.
- [ ] 8. **Per-chore schedules.** Chores that only count on certain weekdays; different goals for school weeks and holidays.
- [ ] 9. **Wallet payout request.** Child taps "request payout", the parent gets an actionable notification, and confirming runs the `adjust_wallet` deduction.
- [ ] 10. **Weekly summary to parents** with per-chore completion counts, not just the points result.

## Robustness and polish

- [ ] 11. **History cap.** 300 entries is only a few weeks. Make it configurable, or add long-term statistics or an export.
- [ ] 12. **Match chores by Maintenance Supporter task ID**, with the name as a fallback, so renaming a task doesn't break matching.
- [ ] 13. **Edge cases.** Catch up a missed 23:59 week close on startup (HA down at the time); check `redeem` with large `units` when the bank can't cover it.
- [ ] 14. **Split `www/kid-chores-cards.js`** (about 1,460 lines) into per-card modules with a small build step.
