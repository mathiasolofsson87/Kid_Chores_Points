# Changelog

All notable changes to Kid Chores & Points. Versions match the git tags and the GitHub releases.

## 1.11.0 – 2026-10-29

### Added
- The History card shows "Missed day forgiven" when the streak grace option forgives a missed day (logged at midnight, once per day).

### Fixed
- A day could be counted as a perfect day (and the day streak go up) in the minutes after midnight, before Maintenance Supporter had updated its task statuses, when every mandatory chore still looked "not due". The day is now unmarked as soon as a chore shows up as due again, and the 23:59:30 check has the final word on the day.
- When a linked chore turns overdue without having been done the day before, that day no longer counts as a perfect day.

## 1.10.0 – 2026-10-25

### Changed
- The Bonus chores card now always lists the bonus chores, also while today's mandatory chores are open. Bonus chores done in the meantime are held as pending and added when the last mandatory chore is done (as before), and are hidden from the list once done or held, whether or not they are linked to a Maintenance Supporter task.
- One banner (styled like the bonus line in the Status card) replaces the old lock hint: "Come on, let's do a first bonus chore!" when there are bonus chores to do, "N bonus points are waiting" while points are held, and a green "N bonus points earned today" once the mandatory chores are done and a bonus chore has been done. It is hidden when there is nothing to do, earn or wait for.
- The "Today's chores done" notification no longer says the bonus chores are unlocked.

## 1.9.0 – 2026-10-25

### Added
- When a parent adjusts points (`adjust_points`) or the wallet (`adjust_wallet`) by hand, the child and the parents now get a notification with the change, the reason text and the new balance, in each recipient's language. Nothing is sent if the balance didn't change. Turn it off under Configure → Notifications → *Notify when points or money are adjusted* (on by default).

## 1.8.3 – 2026-10-23

### Fixed
- In the parents' weekly summary, a chore linked to a Maintenance Supporter task that is only due on some days now shows the days it was due (e.g. `⚠️ Shower 1/2`, `✅ Shower 2/2`) instead of `/7`. The days are recorded as the task becomes due, so the first week after updating may show fewer days than the task really had. Unlinked chores are still out of 7.

## 1.8.2 – 2026-10-23

### Fixed
- Closing the week manually (the `close_week` service) no longer fails with `'wk'` when the history contains entries saved before the week number was recorded. Those entries are skipped in the per-chore breakdown and no longer break reverting.

## 1.8.1 – 2026-10-23

### Fixed
- The Medals tile no longer says to finish today's tasks to keep the streak when no mandatory chore is open (for example when the only open chore is a Maintenance Supporter task that isn't due). The bedtime reminder uses the same check.
- A day with nothing left to do is now marked as a perfect day when the integration starts or is reloaded too, e.g. after relinking a chore to a task or restarting Home Assistant, not only at 23:59:30.

## 1.8.0 – 2026-10-23

### Added
- The parents' weekly summary now lists every chore with how many days it was done (e.g. `⚠️ Trash 1/7`), worst first, plus bonus chores (`⭐ Vacuum ×3`). Chores done every day are folded into one line when the list is long. Reverted changes are not counted. Turn it off under Configure → Goal, policy & currency → *Per-chore breakdown in the weekly summary*.

### Fixed
- A mandatory chore linked to a Maintenance Supporter task that is only due on some days (say showering on Wednesdays and Sundays) no longer holds the other days open. It counts as open only while the task is *due soon*, *overdue* or *triggered*, so the *Mandatory chores remaining* sensor now matches the Chores to do card and bonus chores unlock. If the task's status can't be read it still counts as due. A day with nothing due counts as a perfect day for streaks. Chores not linked to a task are still daily.

### Changed
- Documented that *Automatic* notification language needs a language saved in the person's Home Assistant profile (picked explicitly in Profile → Language); a profile that only follows the browser falls back to the system language. Debug logging now says why a notification language was chosen.

## 1.7.2 – 2026-10-22

### Changed
- The Medals card shows every medal again. The collapsed view with a *Show all medals* button from 1.7.0 is gone.
- The bonus-chore medals are now dinosaur themed instead of space themed: *Dino Egg* / *Dinoägget*, *Stomp Stomp!* / *Stamp, stamp!*, *Fossil Finder* / *Fossiljägaren* and *T-Rex Roar!* / *T-Rex-vrålet*, with new icons (a spotted egg, a footprint, a bone and a roaring T-Rex head). Targets are unchanged and the last medal (250 bonus chores) now pays 50 points instead of 45.

## 1.7.1 – 2026-10-22

### Fixed
- **Notifications now follow the recipient's language.** They were always sent in the Home Assistant system language, so a child whose own profile is set to Swedish still got English notifications. They now use the language of the person's own profile (child and parents separately; the system language if there is none), and Configure → *Notifications* has a new *Language of the child's/parents' notifications* setting to choose English or Swedish explicitly. The Medals and Status cards show medal names in the viewer's own language, too.

## 1.7.0 – 2026-10-22

### Added
- **Streaks and medals.** Optional (Configure → *Streaks & medals*). A **day streak** counts days in a row with every mandatory chore done (today only counts against you once it is over; an optional *forgive one missed day per week*), a **week streak** counts weeks in a row where the goal was reached. 18 **medals** in four tiers (bronze, silver, gold, diamond) are earned for streaks, total chores done and bonus chores done, plus *Treat Yourself!* for the first reward handed out. Streak, chore-count and bonus-chore medals pay bonus points (at most 50) straight into the bank; *Treat Yourself!* is honorary. Targets and bonuses are editable per group; each medal is earned once and reverting the change that earned it takes it back (a closed week can't be reverted). Notifications for the child and the parents, logbook entries, and a "🔥 streak at risk" line in the bedtime reminder. English and Swedish names ("Little Sprout" / "Lilla Grodden", ...).
- **Medals card** (`kid-chores-medals-card`): every earned medal with its date and a NEW tag, plus the next one to earn in each kind with what to do, progress and the bonus; a *Show all medals* button reveals the rest. The **Status card** gets one streak tile (the day or week streak that is closest to its next medal), and the **History card** shows medals.
- New sensors: day streak, week streak, medals, chores done and bonus chores done.

## 1.6.2 – 2026-10-22

### Changed
- **Revert any change, not just the latest.** Every entry in the History card now has a revert button (with a confirmation), replacing the single *Undo* button. Reverting takes back exactly what that entry changed, however long ago, and the entry is marked *Reverted*. New `kid_chores_points.revert` service (by history entry `id`); `undo` now reverts the latest change that can still be reverted. Chores and bonuses from a closed week can't be reverted, and entries made before 1.6.2 have no button. The old limit of 10 steps is gone.

## 1.6.1 – 2026-10-22

### Fixed
- The Rewards card showed nothing after 1.6.0 (a missing import in the new card modules). Added tests for the Rewards and Wallet cards.

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
