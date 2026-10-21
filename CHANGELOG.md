# Changelog

All notable changes to Kid Chores & Points. Versions match the git tags and the GitHub releases.

## 1.6.0 – 2026-10-21

### Added
- **Bedtime reminder.** Set the child's bedtime for school nights (optionally a different one for the weekend, i.e. Fridays and Saturdays) and a lead time under *Configure → Bedtime reminder*. That long before bedtime (5–240 minutes, default 45) the child's device gets a notification such as "2 chores left today: • Dishes (+20 p) • Trash (+30 p)", or "Just one left: Trash (+30 p)". Nothing is sent when all mandatory chores are done, and never more than once a day. English and Swedish.

### Changed
- The dashboard cards are now built from modules in `frontend/src` (esbuild) into the same single served file. Card names and options are unchanged, so dashboards need no changes. Added tests for the cards (jsdom) and a CI check that the built file is current.

## 1.5.0 – 2026-10-21

### Added
- **Undo.** New `kid_chores_points.undo` service and an *Undo* button on the History card. It reverts the latest completed chore, redemption (including cash-outs) or manual adjustment, and can be repeated to step back up to 10 changes. A closed week can't be reopened, so closing the week clears the undo list. Every undo is shown in the history and logbook, and the parents are notified.
- **Swedish config flow.** `translations/sv.json`, so the setup and Configure screens follow the Home Assistant language.
- **Missed week close is caught up.** If Home Assistant was down at 23:59 when the week should have closed, the week is closed on the next start. Changing the first day of the week never triggers an extra close.
- **Chores are linked to Maintenance Supporter tasks by task ID.** A chore picked from the task list keeps working when the task is renamed, and two tasks with the same name on different objects are told apart. Chores typed by hand, or added earlier, still match on the task name; re-pick the task under *Edit a chore* to link them.
- **Configurable history length** (50–1000 entries, default 300) under *Goal, policy & currency*.
- Tests for all of the above (80 in total).

### Fixed
- Editing chores or rewards in Configure could write into the shared default options, so a tracker created later in the same Home Assistant session started with the previous tracker's chores until the next restart.
- The description of the *Bonus chores* settings page showed literal `\n` characters instead of line breaks.

## 1.4.5 – 2026-10-20
- Bonus note on the status card restyled as a banner.
- Added tests (pytest) and CI (hassfest, HACS validation); MIT license.

## 1.4.4 – 2026-10-20
- Shorter bonus banking wording on the status card.

## 1.4.3 – 2026-10-20
- The bonus banking note sits on its own line on the status card.

## 1.4.2 – 2026-10-20
- Fixed the `adjust_points` service registration.

## 1.4.1 – 2026-10-20
- Brand icons and logos (light and dark).

## 1.4.0 – 2026-10-20
- Bonus points are kept out of the weekly goal: the goal is measured on mandatory points only, and the week's bonus points are banked only if it is met.
- Finished chores are hidden from the *Chores to do* and *Bonus chores* cards.

## 1.3.1 – 2026-10-20
- *Edit* step for chores and rewards in Configure.
- Stale entities are cleaned up when chores or rewards are removed.

## 1.3.0 – 2026-10-20
- **Wallet** with cash-out rewards: a reward can pay money into the child's wallet instead of being handed out. New `adjust_wallet` service and Wallet card.

## 1.2.2 – 2026-10-20
- Tapping a chore shows the Maintenance Supporter task notes.

## 1.2.1 – 2026-10-20
- A chore is hidden entirely when its Maintenance Supporter task doesn't match the card's filters.

## 1.2.0 – 2026-10-20
- *Chores to do* and *Bonus chores* cards with Maintenance Supporter buttons.

## 1.1.0 – 2026-10-20
- Points history timeline and the History card.

## 1.0.3 – 2026-10-19
- Only completions made by the child's linked Home Assistant user count.

## 1.0.2 – 2026-10-19
- Adjust points card; the example dashboard uses the custom cards.

## 1.0.1 – 2026-10-19
- Maintenance release.

## 1.0.0 – 2026-10-18
- First release: points from Maintenance Supporter chores, weekly goal and bank, rewards, Rewards and Status cards, configurable first day of the week, notifications and logbook texts in English and Swedish, example dashboard.
