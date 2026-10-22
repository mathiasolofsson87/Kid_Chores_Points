# Kid Chores & Points

A Home Assistant integration that turns chore completions into points, a weekly goal, a points bank, redeemable rewards and a wallet of real money. Built to work with [Maintenance Supporter](https://github.com/iluebbe/maintenance_supporter), but chores can also be completed via a service.

## Install (HACS)

1. HACS → ⋮ → **Custom repositories** → add this repo URL, category **Integration**.
2. Install **Kid Chores & Points**, restart Home Assistant.
3. **Settings → Devices & services → Add integration → Kid Chores & Points**. Give it a name (one per child).
4. Click **Configure** on the integration to set up everything in the UI:
   - **Mandatory chores** – pick a task from the Maintenance Supporter list (free-text names also work) + points. A chore picked from the list is linked to the task's ID, so renaming the task in Maintenance Supporter doesn't break it (the chore keeps its name here). A chore typed by hand, or added before v1.5, matches on the task name instead; open **Edit a chore** and re-pick the task from the list to link it. Counted once per day.
   - **Bonus chores** – pick a task + points. Only paid once all mandatory chores are done that day; earlier completions are held as *pending* and paid out when the last mandatory chore is done. Pending points are dropped at midnight. Unlike mandatory chores, a bonus chore pays every time it is completed. Bonus points are collected separately from the weekly goal and are only banked if the goal is met (see below).
   - **Rewards** – name per unit (e.g. `15 min Xbox`) + point cost. Optionally set **Pays into the wallet** to turn a reward into a cash-out (see [Wallet](#wallet)).
   - **Goal, policy & currency** – first day of the week, weekly goal, extra bank points when reached, what happens if the goal is missed (bank all / bank half / forfeit), and the wallet currency label (default `kr`).
   - **Bedtime reminder** – the child's bedtime (school nights, and optionally a different one for the weekend, meaning Fridays and Saturdays) and how many minutes before it to remind. See [Bedtime reminder](#bedtime-reminder).
   - **Notifications** – pick the child and parents as Home Assistant **persons**; their Companion-app phones are found automatically. Extra `notify` services (tablet, group) can be added too.

In the chores and rewards lists, **Add**, **Edit** and **Remove** are separate menu entries. **Edit** opens a form with the current values (name, points and, for rewards, the payout); changing the name renames the item and keeps its place. Adding a name that already exists is refused – use Edit instead.

Changes apply immediately (the integration reloads, balances are kept).

## Whose completions count

If the child **person** (Configure → Notifications) has a linked Home Assistant user, only chores completed by that user count. A task completed by another user (e.g. a parent) is ignored, so a tracker only rewards its own child. Completions that carry no user (automatic completions, NFC tags) still count. To credit the child for something a parent did, complete the task in Maintenance Supporter with the child as *Completed by*. If no child person is set, or the person has no linked user, every completion counts. The `complete_chore` service always counts.

## How it works

- Listens for `maintenance_supporter_task_completed` (matches the chore by `task_id` when it is linked to a task, otherwise by `task_name`).
- At 23:59 on the day before your configured first day of the week (default: Monday, so Sunday night) the week closes: points move to the bank per the policy and the week counter resets.
- Redeeming a reward deducts its points from the bank. A normal reward adds an item to the **Redeemed rewards** to-do list for a parent to hand out; a cash-out reward adds money to the wallet instead.
- Every change to points or the wallet is kept in the history (the last 300 changes by default; change it under **Configure → Goal, policy & currency → History length**, 50–1000).

## Weekly goal, bonus and the bank

Points are counted in two separate piles during the week:

- **Points this week** – points from **mandatory** chores. Only these count towards the weekly goal and the progress bar.
- **Bonus points this week** – points from **bonus** chores (once released, see above). They never count towards the goal; they just wait to be banked.

When the week closes (23:59 on the day before the first day of the week) both piles are reset to 0 and the bank is credited:

- **Goal reached** (mandatory points ≥ weekly goal): the bank receives the mandatory points **plus the goal bonus plus all bonus points**. The goal bonus is a flat extra amount on top; set it to 0 for none.
- **Goal missed:** the bank receives the mandatory points according to the *missed goal* setting – **all**, **half** (rounded down), or **none** (forfeit). The goal bonus is not paid and **the week's bonus points are lost**.

Example with goal 50, goal bonus 10 and 12 bonus points earned:

| Mandatory points | Goal reached? | Bank receives |
|---|---|---|
| 55 | Yes | 55 + 10 + 12 = **77** |
| 50 | Yes | 50 + 10 + 12 = **72** |
| 40 | No | **40** (bank all) / **20** (bank half) / **0** (forfeit) – the 12 bonus points are lost |

Child and parents are notified when the week closes, including how many bonus points were banked or lost, and the result is kept in the *last week result* sensor. Bonus points collected before updating to this behaviour stay in that week's mandatory total.

## Bedtime reminder

Under Configure → *Bedtime reminder*, set the **School nights** bedtime and how many minutes before it the reminder should go out (default 45, adjustable from 5 to 240). At that time, if any mandatory chores are still open, the child's phone (and any extra child `notify` services) gets a notification listing what's left, e.g. *"Almost bedtime 🌙 – 2 chores left today: • Dishes (+20 p) • Trash (+30 p)"*, or *"Just one left: Trash (+30 p)"* when only one is open. Nothing is sent when all mandatory chores are done, and at most one reminder goes out per day.

An optional **Weekend** bedtime applies on Fridays and Saturdays, the nights before a day off; leave it empty to use the school-night bedtime every night. Clear both times to turn the reminder off. The reminder has to fall on the same evening as the bedtime, so a bedtime just after midnight with a long lead time is refused. The child needs a **person** set under Notifications (or an extra child `notify` service) to receive it.

## Streaks and medals

Optional. Turn it on under Configure → *Streaks & medals* → *Settings*. Counting starts at that moment (chores done earlier don't count), and turning it off pauses counting but keeps what was earned.

- **Day streak:** days in a row on which every mandatory chore is done. Today doesn't break the streak until it is over, so a streak that ran through yesterday still counts. The optional *Forgive one missed day per week* keeps a streak alive over one missed day in each week (the missed day isn't counted).
- **Week streak:** weeks in a row where the weekly goal is reached (checked when the week closes).
- **Medals:** 18 in total, each with a tier (bronze, silver, gold, diamond) and its own icon and name:

| Group | Counts | Medals (targets are the defaults) |
|---|---|---|
| Day streaks | days in a row | 3, 7, 14, 30 |
| Week streaks | weeks in a row | 10, 12, 16, 20 |
| Chores done | chores in total | 25, 100, 250, 500, 1000, plus *Treat Yourself!* for the first reward handed out (a cash-out doesn't count) |
| Bonus chores | bonus chores in total | 10, 50, 100, 250 |

Day- and week-streak, chore and bonus-chore medals pay **bonus points straight into the bank** (never more than 50 each); *Treat Yourself!* is honorary. Defaults range from 5 up to 50 points. Under *Streaks & medals* each group has its own page where you change the target and the bonus of every medal (each target must be higher than the one above it). Medals are earned once: if a streak breaks and starts over, a medal that was already earned isn't paid again. Reverting the change that earned a medal (see [Undo and revert](#undo-and-revert)) takes the medal and its bonus back; a medal for a closed week can't be reverted. Once earned, a medal stays earned even if you later raise its target.

The child and the parents get a notification when a medal is earned (switch off under *Settings*), the logbook and History card show it, and the bedtime reminder adds "🔥 Your 5-day streak is at risk!" when a streak is running and chores are still open. Medals only show on the dashboard when they make sense: bonus-chore medals need a bonus chore, and *Treat Yourself!* needs a reward that is handed out (not just cash-outs).

## Undo and revert

Tapped the wrong chore or redeemed the wrong reward? Every change in the **History card** has a small revert button (↩) – tap it, confirm, and that change is undone, however long ago it was made and whatever has happened since. The `revert` service does the same for a history entry `id` (shown in the *Points history* sensor's `history` attribute), and `undo` reverts the latest change that can still be reverted.

Reverting takes back exactly what that entry changed: a completed chore (including any held bonus points it released, and it can then be completed again), a redemption or cash-out (points back to the bank, the reward removed from the *Redeemed rewards* list, the money taken back from the wallet) or a manual adjustment. Balances never go below zero, so reverting a gift the child has already spent takes back only what is left. Chores and bonuses from a week that has been closed can't be reverted, since a closed week can't be reopened. Each revert is added to the history (the original entry is struck through and marked *Reverted*) and the logbook, and the parents get a notification. Entries made before this feature existed have no revert button.

## Wallet

The wallet holds the child's real money, separate from points. Points go in, money comes out of a reward:

1. **Configure → Rewards → Add a reward** (or **Edit a reward** for an existing one). Set the point cost and **Pays into the wallet (per unit)**. For example `Cash out`, cost `10`, pays `5` means *10 points = 5 kr*. Add several cash-out rewards for different rates (e.g. `50 kr` costing `100` points and paying `50`).
2. The child redeems it like any reward (Rewards card or the `redeem` service). The points leave the bank, the money is added to the wallet, and both the child and the parents get a notification with the new balance. Nothing is added to the *Redeemed rewards* list, since there is nothing to hand over.
3. When the parent pays the money out, deduct it with the **Adjust points** card (choose *Wallet*, enter e.g. `-20`) or the `adjust_wallet` service. The same card or service can also add money (a gift, an allowance).

Good to know:

- Amounts are whole numbers and the wallet never goes below 0.
- The currency (default `kr`) is only a label; there is no conversion.
- The Rewards card redeems one unit per tap, so make the unit a sensible amount. The `redeem` service accepts `units` for more.
- Changing a reward's payout only affects future redemptions. Setting the payout to 0 turns a cash-out back into a normal reward.
- The child sees the balance on the **Wallet** card (and as a tile on the Status card once the wallet is in use). The History card shows cash-outs and adjustments, and the *Wallet* sensor can be used in automations.

## Language

Notifications, logbook entries and the "last week result" text use the Home Assistant system language (**Settings → System → General**). English and Swedish are included; other languages fall back to English. The dashboard cards follow each user's own language.

Notifications are sent in the language of the person who gets them: under Configure → *Notifications* the **language of the child's notifications** and the **language of the parents' notifications** are *Automatic* by default, which means the language in that person's own Home Assistant profile (the user linked to the person you selected; with several parents they must all agree), or the system language if there is none. Choose English or Swedish there to always use that one. The logbook, the history and the *last week result* sensor stay in the system language.

## Entities (per tracker)

- **Sensors:** points this week (mandatory only), bonus points this week, points bank, **wallet** (unit = your currency), weekly goal, points to goal, week progress, points today, mandatory chores remaining (attributes list remaining/done chores and the configured chores), pending bonus points, points history (the `history` attribute holds the timeline), last week result. With streaks and medals: **day streak** and **week streak** (best streak, whether it is at risk, the next medal), **medals** (the number earned; the `medals` attribute lists every medal with its target, bonus, progress and date earned), **chores done** and **bonus chores done**.
- **Binary sensors:** mandatory chores complete, and `can afford <reward>` for each reward (attributes: cost, payout, bank).
- **To-do:** redeemed rewards.

## Services

| Service | Purpose |
|---|---|
| `kid_chores_points.complete_chore` | Mark a chore done manually (`name`) |
| `kid_chores_points.redeem` | `reward`, `units` |
| `kid_chores_points.adjust_points` | `target` (week/bank), `points` (±), `reason` |
| `kid_chores_points.adjust_wallet` | `amount` (±, whole numbers), `reason` |
| `kid_chores_points.close_week` | Close the week now |
| `kid_chores_points.undo` | Revert the latest change that can still be reverted (see [Undo and revert](#undo-and-revert)) |
| `kid_chores_points.revert` | Revert any history entry by its `id` (see [Undo and revert](#undo-and-revert)) |

With more than one tracker, pass `config_entry` to pick which one.

## Dashboard cards

The integration ships its own dashboard cards – no extra install or resource setup. In the dashboard editor choose **Add card → Kid Chores & Points – …**:

| Card | For | Purpose |
|---|---|---|
| Status | child | Weekly progress, points, bank and wallet |
| Chores to do | child | Today's mandatory chores with **Done** buttons |
| Bonus chores | child | Bonus chores, unlocked when the mandatory ones are done |
| Rewards | child | Redeem rewards and cash out points |
| Wallet | child | Current money and recent activity |
| Medals | child | Streaks and medals: earned ones, and what to do for the next |
| Adjust points | parent | Add or deduct points in the bank/week or money in the wallet |
| History | parent | Timeline of every change |

With several trackers, pick which one in each card's editor (`device:`). If a card doesn't appear after installing/updating, restart Home Assistant and hard-refresh the browser. English and Swedish texts are built in and follow the user's language.

### Status card

Shows one child's overview: the weekly goal, a progress bar towards it (red < 50 %, yellow ≥ 50 %, green at 100 %), the bonus points collected so far this week right under the bar ("banked when the goal is reached", or "will be banked" once the goal is met; shown when you have bonus chores), tiles for *this week* (mandatory points), *left to goal*, *today* (all points) and the *points bank*, the *wallet* once it is in use (a cash-out reward is configured, or there is money in it), and last week's result once there is one. With [streaks and medals](#streaks-and-medals) turned on it also shows one streak tile: the day or week streak that is closest to its next medal (a week counts as 7 days), how far off that medal is, and a warning when the day streak is at risk. `title:` is optional.

Optional shortcut chips (YAML only), e.g. a button to the parents' view that only some users see:

```yaml
type: custom:kid-chores-status-card
chips:
  - icon: mdi:shield-account
    label: Parents
    navigation_path: parents
    users: [<ha user id>, <ha user id>]   # omit to show to everyone
```

### Medals card

The child's medals, grouped as *Streaks*, *Chores* and *Bonus chores*. It shows every earned medal in colour with the date it was earned (and a **NEW** tag for two days), plus the next one still to earn in each kind, greyed out with what to do, how far along the child is and what it pays. A **Show all medals** button reveals the rest. Groups that don't apply to your setup are left out. It says how to switch the feature on while it is off. `title:` is optional.

### Chores to do card

Each mandatory chore that is still open is one line with its points; a chore disappears from the list as soon as it is done. Chores that are still open and due in Maintenance Supporter get a **Done** button (calls `maintenance_supporter.complete` as the logged-in user, so the usual child-user rule applies). Maintenance Supporter tasks with the label but not in your mandatory list are added as extra lines. When everything is done a "great job" line is shown.

If the Maintenance Supporter task has **notes**, the chore shows an info icon; tap the chore to expand or collapse the notes (both this card and the Bonus card).

A chore that also exists as a Maintenance Supporter task is only shown while that task matches the label and status filters (done chores are not shown); a chore with no Maintenance Supporter task is always shown.

Options (all also in the card editor – labels are offered from your Maintenance Supporter tasks, and you can type others): `title`, `device`, `filter_labels` (Maintenance Supporter labels to include, default `[mandatory]`; `[]` for all tasks), `filter_status` (default `[overdue, triggered, due_soon]`). A task that needs a checklist, readings or a tag scan can't be completed with the button and shows the error instead – complete those in Maintenance Supporter itself.

### Bonus chores card

The bonus counterpart of the *Chores to do* card. While today's mandatory chores are open it shows only the lock hint ("Bonus chores unlock when today's chores are done") and, if any bonus points are being held, how many are waiting. Once the mandatory chores are done it lists your bonus chores with their points (a bonus chore you've already done today is hidden), plus **Done** buttons for the matching Maintenance Supporter tasks. Options and editor are the same as the *Chores to do* card, except `filter_labels` defaults to `[bonus]`.

### Rewards card

- Lists the rewards you configured, with the point cost and an icon (cash-out rewards get a cash icon; others are guessed from the name, e.g. Xbox, screen time, money, falling back to a gift – override with `icons:` in YAML, keyed by the exact reward name), and shows the current bank balance. Cash-out rewards also show what they pay, e.g. `10 points → 5 kr`.
- Only affordable rewards are shown (set `show_unaffordable: true` to also show the rest greyed out). When nothing is affordable it shows a "collect more points" hint listing each reward and its cost on its own line (turn it off with `show_hint: false` or the switch in the card editor).
- Tapping a reward asks for confirmation inline, then redeems one unit.
- `title:` and `color:` can be overridden.

```yaml
type: custom:kid-chores-rewards-card
# optional:
# title: Spend your points
# color: "#30d158"
# show_unaffordable: false
# show_hint: true
# icons:
#   15 min Xbox: mdi:microsoft-xbox
```

### Wallet card

A big balance with the child's current money, and the most recent cash-outs and parent adjustments below it. Options: `title`, `device` (both in the card editor) and `limit` (YAML; activity entries to show, default 5).

### Adjust points card

A parent tool in one card: choose **Bank**, **This week** (the mandatory points that count towards the goal) or **Wallet**, type a number (`5` to add, `-5` to deduct), optionally a reason (shown in the logbook), and press **Apply**. Points totals and the wallet never go below 0. Put it on a parents-only view.

### History card

A parent timeline of every change, newest first and grouped by day: completed chores, bonus chores (including ones held as pending and later released), redeemed rewards and cash-outs (with the money received), manual adjustments of points and the wallet with their reason, and week closes. Each entry shows the amount, the reason/label and (optionally) the week (with bonus), bank and wallet balance afterwards. Each change has a revert button; reverted changes are struck through and an *Undone* entry is added. The number of changes kept is set in Configure (default 300). Options (YAML): `limit` (entries per page, default 30), `show_balances: false` to hide the balances, `title`, `device`. The data is also available as the `history` attribute of the *Points history* sensor.

## Development

The dashboard cards are written as modules in `frontend/src` and bundled into the single file the integration serves, `custom_components/kid_chores_points/www/kid-chores-cards.js`. **Edit the sources, not the built file**, then rebuild and commit both:

```
npm install
npm run build   # bundles frontend/src into the served file
npm test        # card tests (jsdom)
```

Python tests: see `requirements_test.txt` and run `pytest`. CI fails if the built card file doesn't match `frontend/src`.

## Maintenance Supporter labels

Points are awarded by task (its ID, or its name for chores that aren't linked), so any configured chore counts when completed. The *Chores to do* and *Bonus chores* cards, however, only show Maintenance Supporter tasks (and their **Done** buttons) that match a **label**: give your mandatory tasks the label `mandatory` and your bonus tasks the label `bonus` in Maintenance Supporter, or change `filter_labels` on the cards. Without a matching label a task isn't listed by the card (a configured chore that has no Maintenance Supporter task is still shown).

## Example dashboard

[`examples/dashboard.yaml`](examples/dashboard.yaml) is a ready-made dashboard with a child view (Status, Chores to do, Bonus chores, Rewards and Wallet cards) and a parent view (settings shortcut, Status, Adjust points, History, the *Redeemed rewards* list and a logbook). It uses only the built-in cards, so there is nothing to install besides Maintenance Supporter itself.

To use it: **Settings → Dashboards → Add dashboard → New dashboard from scratch**, open it, **⋮ → Raw configuration editor**, and paste the file. Read the `EDIT` notes at the top – the to-do list and logbook entity ids assume the tracker is named `Chores`, and the parent view needs your user ids.

## Migrating from the YAML package

Remove the package, then re-enter chores/rewards in the UI. The old balances can be carried over with `adjust_points`.
