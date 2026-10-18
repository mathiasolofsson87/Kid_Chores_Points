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

## Maintenance Supporter labels

Points are awarded by task name, so any configured chore counts when completed. The example dashboard, however, shows Maintenance Supporter's task lists filtered by **label**: give your mandatory tasks the label `mandatory` and your bonus tasks the label `bonus` in Maintenance Supporter, or they won't appear in the dashboard lists.

## Example dashboard

[`examples/dashboard.yaml`](examples/dashboard.yaml) is a ready-made dashboard with a child view (weekly progress, today's chores, bonus chores, reward buttons) and a parent view (settings shortcut, point adjustments, rewards to hand out). The child view uses the [Maintenance Supporter card](https://github.com/iluebbe/maintenance_supporter) for completing chores; remove those cards if you complete chores another way.

To use it: **Settings → Dashboards → Add dashboard → New dashboard from scratch**, open it, **⋮ → Raw configuration editor**, and paste the file. Read the `EDIT` notes at the top – entity ids assume the tracker is named `Chores`, the reward buttons assume rewards named `10 kr`, `15 min Xbox` and `15 min screen time`, and the parent view needs your user ids.
