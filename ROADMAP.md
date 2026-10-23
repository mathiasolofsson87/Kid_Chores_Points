# Roadmap / ideas

Suggestions noted on 2026-10-20 (at v1.4.5). Tick items off as they are done.

Suggested order: 1 + 2, then 3, then 13, then 5 and 6.

## Reliability and quality

- [x] 1. **Tests.** (done: 47 tests in `tests/`; run with `.venv/bin/python -m pytest`, setup: `uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -r requirements_test.txt`) Add `tests/` with pytest and `pytest-homeassistant-custom-component`. Cover week close, bonus banking, the missed-goal policies (all / half / forfeit), wallet floor at 0 and pending bonus dropped at midnight.
- [x] 2. **CI.** (done: `.github/workflows/validate.yml`, needs a first run on GitHub to confirm) GitHub Actions with hassfest, HACS validation and pytest.
- [x] 3. **Swedish config flow.** (done: `translations/sv.json`) Add `translations/sv.json`; only `en.json` exists, so the config and options flow is English-only.
- [x] 4. **Releases and changelog.** (done: `CHANGELOG.md`, and every tag has a GitHub release with notes) Tagged GitHub releases with short notes, so HACS users see what changed.

## Features

- [x] 5. **Undo.** (done: `undo` service and an Undo button on the History card; steps back up to 10 changes, not across a week close) Revert a mistaken completion or redemption, e.g. a revert action on History card entries.
- [ ] 6. **Parent approval mode.** Optional: a "Done" tap goes to pending and a parent confirms it via an actionable notification.
- [x] 7. **Streaks and badges.** (done as streaks and medals: day and week streaks, 18 medals, Medals card; see `CHANGELOG.md` 1.7.0) E.g. 7 days in a row, or all chores every day of the week, with an optional point bonus.
- [ ] 8. **Per-chore schedules.** Chores that only count on certain weekdays; different goals for school weeks and holidays.
- [ ] 9. **Wallet payout request.** Child taps "request payout", the parent gets an actionable notification, and confirming runs the `adjust_wallet` deduction.
- [x] 10. **Weekly summary to parents** (done: per-chore counts in the week-close notification, optional) with per-chore completion counts, not just the points result.
- [ ] 15. **Reward entity picker.** Let each reward optionally link to an entity (e.g. a smart outlet). Example: "15 min more Xbox time" → `switch.xbox_outlet`. Redeeming the reward should turn the entity on automatically for the reward's duration, then off again. *(Added 2026-10-21.)*
- [x] 16. **Bedtime reminder.** (done: Configure → Bedtime reminder) Let the parent set the child's bedtime (possibly different on school nights and weekends) and a lead time, e.g. 45 minutes. That long before bedtime, the child's device gets a notification if any mandatory chores are still open that day, listing what's left. Nothing is sent when all are done. *(Added 2026-10-21.)*
- [ ] 17. **"Re-check today" button.** A button entity on the child's device plus a `recheck_today` action. It re-runs the "nothing left to do" check (mark the day perfect, refresh sensors and cards) and awards a day-streak medal at once, for when something doesn't update on its own, e.g. after editing a Maintenance Supporter task. No startup delay is needed: the status listener already re-checks when the task sensors come up. *(Added 2026-10-23.)*

## Robustness and polish

- [x] 11. **History cap.** (done: configurable 50–1000 under Goal, policy & currency; no export or long-term statistics) 300 entries is only a few weeks. Make it configurable, or add long-term statistics or an export.
- [x] 12. **Match chores by Maintenance Supporter task ID** (done: chores picked from the task list are linked by ID; hand-typed or older chores still match by name), with the name as a fallback, so renaming a task doesn't break matching.
- [x] 13. **Edge cases.** (done: missed week close is caught up on start, huge `units` are covered by a test) Catch up a missed 23:59 week close on startup (HA down at the time); check `redeem` with large `units` when the bank can't cover it.
- [x] 14. **Split `www/kid-chores-cards.js`** (done: modules in `frontend/src`, esbuild bundle, jsdom tests, CI check) (about 1,460 lines) into per-card modules with a small build step.
