# Kid Chores & Points

A Home Assistant integration that turns chore completions into points, a weekly goal, a points bank, redeemable rewards and a wallet of real money. Built to work with [Maintenance Supporter](https://github.com/iluebbe/maintenance_supporter), but chores can also be completed via a service.

## Install (HACS)

1. HACS → ⋮ → **Custom repositories** → add this repo URL, category **Integration**.
2. Install **Kid Chores & Points**, restart Home Assistant.
3. **Settings → Devices & services → Add integration → Kid Chores & Points**. Give it a name (one per child).
4. Click **Configure** on the integration to set up everything in the UI:
   - **Mandatory chores** – pick a task from the Maintenance Supporter list (free-text names also work) + points. Matching is by task name, so if you rename a task in Maintenance Supporter, use **Edit a chore** and pick the new name. Counted once per day.
   - **Bonus chores** – pick a task + points. Only paid once all mandatory chores are done that day; earlier completions are held as *pending* and paid out when the last mandatory chore is done. Pending points are dropped at midnight. Unlike mandatory chores, a bonus chore pays every time it is completed. Bonus points are collected separately from the weekly goal and are only banked if the goal is met (see below).
   - **Rewards** – name per unit (e.g. `15 min Xbox`) + point cost. Optionally set **Pays into the wallet** to turn a reward into a cash-out (see [Wallet](#wallet)).
   - **Goal, policy & currency** – first day of the week, weekly goal, extra bank points when reached, what happens if the goal is missed (bank all / bank half / forfeit), and the wallet currency label (default `kr`).
   - **Notifications** – pick the child and parents as Home Assistant **persons**; their Companion-app phones are found automatically. Extra `notify` services (tablet, group) can be added too.

In the chores and rewards lists, **Add**, **Edit** and **Remove** are separate menu entries. **Edit** opens a form with the current values (name, points and, for rewards, the payout); changing the name renames the item and keeps its place. Adding a name that already exists is refused – use Edit instead.

Changes apply immediately (the integration reloads, balances are kept).

## Whose completions count

If the child **person** (Configure → Notifications) has a linked Home Assistant user, only chores completed by that user count. A task completed by another user (e.g. a parent) is ignored, so a tracker only rewards its own child. Completions that carry no user (automatic completions, NFC tags) still count. To credit the child for something a parent did, complete the task in Maintenance Supporter with the child as *Completed by*. If no child person is set, or the person has no linked user, every completion counts. The `complete_chore` service always counts.

## How it works

- Listens for `maintenance_supporter_task_completed` (uses `task_name`).
- At 23:59 on the day before your configured first day of the week (default: Monday, so Sunday night) the week closes: points move to the bank per the policy and the week counter resets.
- Redeeming a reward deducts its points from the bank. A normal reward adds an item to the **Redeemed rewards** to-do list for a parent to hand out; a cash-out reward adds money to the wallet instead.
- Every change to points or the wallet is kept in the history (the last 300 changes).

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

## Entities (per tracker)

- **Sensors:** points this week (mandatory only), bonus points this week, points bank, **wallet** (unit = your currency), weekly goal, points to goal, week progress, points today, mandatory chores remaining (attributes list remaining/done chores and the configured chores), pending bonus points, points history (the `history` attribute holds the timeline), last week result.
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
| Adjust points | parent | Add or deduct points in the bank/week or money in the wallet |
| History | parent | Timeline of every change |

With several trackers, pick which one in each card's editor (`device:`). If a card doesn't appear after installing/updating, restart Home Assistant and hard-refresh the browser. English and Swedish texts are built in and follow the user's language.

### Status card

Shows one child's overview: the weekly goal, a progress bar towards it (red < 50 %, yellow ≥ 50 %, green at 100 %), the bonus points collected so far this week right under the bar ("banked when the goal is reached", or "will be banked" once the goal is met; shown when you have bonus chores), tiles for *this week* (mandatory points), *left to goal*, *today* (all points) and the *points bank*, the *wallet* once it is in use (a cash-out reward is configured, or there is money in it), and last week's result once there is one. `title:` is optional.

Optional shortcut chips (YAML only), e.g. a button to the parents' view that only some users see:

```yaml
type: custom:kid-chores-status-card
chips:
  - icon: mdi:shield-account
    label: Parents
    navigation_path: parents
    users: [<ha user id>, <ha user id>]   # omit to show to everyone
```

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

A parent timeline of every change, newest first and grouped by day: completed chores, bonus chores (including ones held as pending and later released), redeemed rewards and cash-outs (with the money received), manual adjustments of points and the wallet with their reason, and week closes. Each entry shows the amount, the reason/label and (optionally) the week (with bonus), bank and wallet balance afterwards. The last 300 changes are kept. Options (YAML): `limit` (entries per page, default 30), `show_balances: false` to hide the balances, `title`, `device`. The data is also available as the `history` attribute of the *Points history* sensor.

## Maintenance Supporter labels

Points are awarded by task name, so any configured chore counts when completed. The *Chores to do* and *Bonus chores* cards, however, only show Maintenance Supporter tasks (and their **Done** buttons) that match a **label**: give your mandatory tasks the label `mandatory` and your bonus tasks the label `bonus` in Maintenance Supporter, or change `filter_labels` on the cards. Without a matching label a task isn't listed by the card (a configured chore that has no Maintenance Supporter task is still shown).

## Example dashboard

[`examples/dashboard.yaml`](examples/dashboard.yaml) is a ready-made dashboard with a child view (Status, Chores to do, Bonus chores, Rewards and Wallet cards) and a parent view (settings shortcut, Status, Adjust points, History, the *Redeemed rewards* list and a logbook). It uses only the built-in cards, so there is nothing to install besides Maintenance Supporter itself.

To use it: **Settings → Dashboards → Add dashboard → New dashboard from scratch**, open it, **⋮ → Raw configuration editor**, and paste the file. Read the `EDIT` notes at the top – the to-do list and logbook entity ids assume the tracker is named `Chores`, and the parent view needs your user ids.

## Migrating from the YAML package

Remove the package, then re-enter chores/rewards in the UI. The old balances can be carried over with `adjust_points`.
