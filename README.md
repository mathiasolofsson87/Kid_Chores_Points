# Kid Chores & Points

A Home Assistant integration that turns chore completions into points, a weekly goal, a points bank and redeemable rewards. Built to work with [Maintenance Supporter](https://github.com/iluebbe/maintenance_supporter), but chores can also be completed via a service.

## Install (HACS)

1. HACS → ⋮ → **Custom repositories** → add this repo URL, category **Integration**.
2. Install **Kid Chores & Points**, restart Home Assistant.
3. **Settings → Devices & services → Add integration → Kid Chores & Points**. Give it a name (one per child).
4. Click **Configure** on the integration to set up everything in the UI:
   - **Mandatory chores** – pick a task from the Maintenance Supporter list (free-text names also work) + points. Matching is by task name, so if you rename a task in Maintenance Supporter, re-pick it here. Counted once per day.
   - **Bonus chores** – only paid once all mandatory chores are done that day; earlier completions are held as *pending* and paid out when the last mandatory chore is done. Pending points are dropped at midnight.
   - **Rewards** – name per unit (e.g. `15 min Xbox`) + point cost.
   - **Weekly goal & policy** – first day of the week, goal, extra bank points when reached, and what happens if missed (bank all / bank half / forfeit).
   - **Notifications** – pick the child and parents as Home Assistant **persons**; their Companion-app phones are found automatically. Extra `notify` services (tablet, group) can be added too.

Changes apply immediately (the integration reloads, balances are kept).

## Whose completions count

If the child **person** (Configure → Notifications) has a linked Home Assistant user, only chores completed by that user count. A task completed by another user (e.g. a parent) is ignored, so a tracker only rewards its own child. Completions that carry no user (automatic completions, NFC tags) still count. To credit the child for something a parent did, complete the task in Maintenance Supporter with the child as *Completed by*. If no child person is set, or the person has no linked user, every completion counts. The `complete_chore` service always counts.

## How it works

- Listens for `maintenance_supporter_task_completed` (uses `task_name`).
- At 23:59 on the day before your configured first day of the week (default: Monday, so Sunday night) the week closes: points move to the bank per the policy and the week counter resets.
- Redeeming a reward deducts from the bank and adds an item to the **Redeemed rewards** to-do list for a parent to hand out.

## Weekly goal, bonus and the bank

When the week closes (23:59 on the day before the first day of the week), the week's points move to the bank and the weekly counter resets to 0.

- **Goal reached** (points this week ≥ weekly goal): the bank receives the week's points **plus the goal bonus**. The bonus is a flat amount on top of the points earned. Set it to 0 for no bonus.
- **Goal missed:** the bank receives points according to the *missed goal* setting – **all** points, **half** (rounded down), or **none** (forfeit). No bonus is paid.

Example with goal 50 and bonus 10:

| Points earned | Goal reached? | Bank receives |
|---|---|---|
| 55 | Yes | 55 + 10 = **65** |
| 50 | Yes | 50 + 10 = **60** |
| 40 | No | **40** (bank all) / **20** (bank half) / **0** (forfeit) |

The bonus only shows up in the bank and in the *last week result* sensor, never in *points this week*. Both child and parents are notified when the week closes.

## Language

Notifications, logbook entries and the "last week result" text use the Home Assistant system language (**Settings → System → General**). English and Swedish are included; other languages fall back to English. The dashboard cards follow each user's own language.

## Entities (per tracker)

Sensors: points this week, points bank, weekly goal, points to goal, week progress, points today, mandatory chores remaining (attributes list remaining/done), pending bonus points, last week result.
Binary sensors: mandatory chores complete, `can afford <reward>` for each reward.
To-do: redeemed rewards.

## Services

| Service | Purpose |
|---|---|
| `kid_chores_points.complete_chore` | Mark a chore done manually (`name`) |
| `kid_chores_points.redeem` | `reward`, `units` |
| `kid_chores_points.adjust_points` | `target` (week/bank), `points` (±), `reason` |
| `kid_chores_points.close_week` | Close the week now |

With more than one tracker, pass `config_entry` to pick which one.

## Migrating from the YAML package

Remove the package, then re-enter chores/rewards in the UI. The old balances can be carried over with `adjust_points`.

## Status card

**Add card → Kid Chores & Points – Status** shows one child's overview: the weekly goal, a progress bar towards it (red < 50 %, yellow ≥ 50 %, green at 100 %), tiles for *this week*, *left to goal*, *today* and the *points bank*, and last week's result once there is one. Pick which child's tracker to show in the card editor (`device:`); `title:` is optional. English and Swedish texts follow the user's language.

Optional shortcut chips (YAML only), e.g. a button to the parents' view that only some users see:

```yaml
type: custom:kid-chores-status-card
chips:
  - icon: mdi:shield-account
    label: Parents
    navigation_path: parents
    users: [<ha user id>, <ha user id>]   # omit to show to everyone
```

## Adjust points card

**Add card → Kid Chores & Points – Adjust points** is a parent tool in one card: choose **Bank** or **This week**, type a number (`5` to add, `-5` to deduct), optionally a reason (shown in the logbook), and press **Apply**. Totals never go below 0. Pick the child's tracker in the card editor (`device:`). Put it on a parents-only view.

## Chores to do card

**Add card → Kid Chores & Points – Chores to do** replaces the markdown list and the Maintenance Supporter card for the mandatory chores. Each configured mandatory chore is one line: ticked and struck through when done, with its points. Chores that are still open and due in Maintenance Supporter get a **Done** button (calls `maintenance_supporter.complete` as the logged-in user, so the usual child-user rule applies). Maintenance Supporter tasks with the label but not in your mandatory list are added as extra lines. When everything is done a "great job" line is shown.

Options (all also in the card editor – labels are offered from your Maintenance Supporter tasks, and you can type others): `title`, `device`, `filter_labels` (Maintenance Supporter labels to include, default `[mandatory]`; `[]` for all tasks), `filter_status` (default `[overdue, triggered, due_soon]`). A task that needs a checklist, readings or a tag scan can't be completed with the button and shows the error instead – complete those in the Maintenance Supporter card.

## Bonus chores card

**Add card → Kid Chores & Points – Bonus chores** is the bonus counterpart of the *Chores to do* card. While today's mandatory chores are open it shows only the lock hint ("Bonus chores unlock when today's chores are done") and, if any bonus points are being held, how many are waiting. Once the mandatory chores are done it lists your bonus chores with their points, plus **Done** buttons for the matching Maintenance Supporter tasks. Options and editor are the same as the *Chores to do* card, except `filter_labels` defaults to `[bonus]`.

## History card

**Add card → Kid Chores & Points – History** is a parent timeline of every points change, newest first and grouped by day: completed chores, bonus chores (including ones held as pending and later released), redeemed rewards, manual adjustments with their reason, and week closes. Each entry shows the points, the reason/label and (optionally) the week and bank balance afterwards. The last 300 changes are kept; history starts when you update. Options (YAML): `limit` (entries per page, default 30), `show_balances: false` to hide the balances, `title`, `device`. The data is also available as the `history` attribute of the *Points history* sensor.

## Rewards card

The integration ships its own dashboard cards (Status, Rewards, Adjust points, Chores to do, Bonus chores, History) – no extra install or resource setup. In the dashboard editor choose **Add card → Kid Chores & Points – Rewards**.

- Lists the rewards you configured, with the point cost and an icon (guessed from the name, e.g. Xbox, screen time, money – override with `icons:` in YAML), and shows the current bank balance.
- Only affordable rewards are shown (set `show_unaffordable: true` to also show the rest greyed out). When nothing is affordable it shows a "collect more points" hint listing each reward and its cost on its own line (turn it off with `show_hint: false` or the switch in the card editor).
- Tapping a reward asks for confirmation inline, then redeems it.
- With several trackers, pick which one in the card editor (`device:`). English and Swedish texts are built in (follows the user's language); `title:` and `color:` can be overridden.

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

If the card doesn't appear after installing/updating, restart Home Assistant and hard-refresh the browser.

## Maintenance Supporter labels

Points are awarded by task name, so any configured chore counts when completed. The example dashboard, however, shows Maintenance Supporter's task lists filtered by **label**: give your mandatory tasks the label `mandatory` and your bonus tasks the label `bonus` in Maintenance Supporter, or they won't appear in the dashboard lists.

## Example dashboard

[`examples/dashboard.yaml`](examples/dashboard.yaml) is a ready-made dashboard with a child view (weekly progress, today's chores, bonus chores, reward buttons) and a parent view (settings shortcut, point adjustments, rewards to hand out). The child view uses the [Maintenance Supporter card](https://github.com/iluebbe/maintenance_supporter) for completing chores; remove those cards if you complete chores another way.

To use it: **Settings → Dashboards → Add dashboard → New dashboard from scratch**, open it, **⋮ → Raw configuration editor**, and paste the file. Read the `EDIT` notes at the top – entity ids assume the tracker is named `Chores`, the reward buttons assume rewards named `10 kr`, `15 min Xbox` and `15 min screen time`, and the parent view needs your user ids.
