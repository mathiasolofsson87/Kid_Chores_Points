import assert from "node:assert/strict";
import { test } from "node:test";

import { loadCards, makeHass, mount } from "./harness.mjs";

const win = loadCards();

const CARDS = ["rewards", "status", "adjust", "history", "todo", "bonus", "wallet", "medals"];

test("every card and its editor is registered", () => {
  for (const name of CARDS) {
    assert.ok(win.customElements.get(`kid-chores-${name}-card`), `${name} card`);
    assert.ok(win.customElements.get(`kid-chores-${name}-card-editor`), `${name} editor`);
  }
});

test("every card is offered in the dashboard card picker", () => {
  const types = Array.from(win.customCards, (c) => c.type).sort();
  assert.deepEqual(types, CARDS.map((n) => `kid-chores-${n}-card`).sort());
});

// ---------------------------------------------------------------------
// History card and Undo
// ---------------------------------------------------------------------
const entry = (extra = {}) => ({
  id: "e1",
  group: "e1",
  can_revert: true,
  t: "2026-10-21T10:00:00+00:00",
  type: "chore",
  label: "Dishes",
  points: 20,
  target: "week",
  pending: 0,
  week: 20,
  week_bonus: 0,
  bank: 0,
  amount: 0,
  wallet: 0,
  ...extra,
});

const historyHass = (history) =>
  makeHass({
    sensors: {
      points_bank: {},
      points_history: { state: String(history.length), attributes: { history } },
    },
  });

test("every revertable history entry has a revert button that asks first", async () => {
  const history = [entry({ id: "e2", group: "e2", label: "Trash" }), entry()];
  const hass = historyHass(history);
  const card = await mount(win, "kid-chores-history-card", {}, hass);
  const buttons = card.shadowRoot.querySelectorAll(".rev");
  assert.equal(buttons.length, 2);
  buttons[1].click(); // the older entry, not the latest
  assert.match(card.shadowRoot.textContent, /Revert "Dishes"\?/);
  assert.deepEqual(hass.calls, []);
  card.shadowRoot.querySelector(".yes").click();
  await new Promise((r) => setTimeout(r, 0));
  assert.deepEqual(hass.calls, [
    { domain: "kid_chores_points", service: "revert", data: { id: "e1", config_entry: "entry-1" } },
  ]);
});

test("declining the confirmation reverts nothing", async () => {
  const hass = historyHass([entry()]);
  const card = await mount(win, "kid-chores-history-card", {}, hass);
  card.shadowRoot.querySelector(".rev").click();
  card.shadowRoot.querySelector(".no").click();
  assert.deepEqual(hass.calls, []);
  assert.ok(card.shadowRoot.querySelector(".rev"));
});

test("entries that can't be reverted have no button; reverted ones are marked", async () => {
  const history = [
    entry({ id: "e3", group: "e3", can_revert: false, type: "week_close", label: "20/50" }),
    entry({ id: "e2", group: "e2", can_revert: false, reverted: true, label: "Trash" }),
    entry({ id: "e1b", group: "e1", can_revert: false, type: "bonus_released", label: "Vacuum" }),
  ];
  const card = await mount(win, "kid-chores-history-card", {}, historyHass(history));
  assert.equal(card.shadowRoot.querySelector(".rev"), null);
  assert.equal(card.shadowRoot.querySelectorAll(".row.reverted").length, 1);
  assert.match(card.shadowRoot.textContent, /Reverted/);
});

test("history card lists undone changes", async () => {
  const history = [entry({ type: "undo", label: "Dishes", points: -20, can_revert: false }), entry({ reverted: true, can_revert: false })];
  const card = await mount(win, "kid-chores-history-card", {}, historyHass(history));
  const text = card.shadowRoot.textContent;
  assert.match(text, /Undone/);
  assert.match(text, /-20 p/);
});

test("history card follows the user's language", async () => {
  const hass = historyHass([entry()]);
  hass.language = "sv";
  const card = await mount(win, "kid-chores-history-card", {}, hass);
  assert.match(card.shadowRoot.querySelector(".rev").title, /Ångra/);
});

// ---------------------------------------------------------------------
// Chores to do: pairing chores with Maintenance Supporter tasks
// ---------------------------------------------------------------------
const task = (id, name, extra = {}) => ({
  id,
  name,
  sensor_entity_id: `sensor.ms_${id}`,
  status: "due_soon",
  labels: ["mandatory"],
  ...extra,
});

const todoHass = ({ remaining, chores, ids = {}, tasks }) =>
  makeHass({
    sensors: {
      mandatory_remaining: {
        attributes: { remaining, mandatory_chores: chores, bonus_chores: {}, chore_ids: ids },
      },
      points_today: { attributes: { bonus_done: [], mandatory_done: [], pending: [] } },
    },
    objects: [{ object: { name: "Kitchen" }, tasks }],
  });

const bonusHass = ({ bonus_chores, pending, tasks = [] }) =>
  makeHass({
    sensors: {
      mandatory_remaining: {
        attributes: { remaining: ["Dishes"], mandatory_chores: { Dishes: 20 }, bonus_chores, chore_ids: {} },
      },
      points_today: { attributes: { bonus_done: [], mandatory_done: [], pending } },
      pending_bonus: { state: String(pending.reduce((sum, p) => sum + p.points, 0)) },
    },
    objects: [{ object: { name: "Kitchen" }, tasks }],
  });

test("the bonus card lists bonus chores while mandatory chores are open, without the ones already held", async () => {
  const hass = bonusHass({ bonus_chores: { Vacuum: 5, Weeds: 10 }, pending: [{ name: "Weeds", points: 10 }] });
  const card = await mount(win, "kid-chores-bonus-card", {}, hass);
  assert.deepEqual(rowNames(card), ["Vacuum"]);
  const hints = card.shadowRoot.querySelectorAll(".bonus"); // one combined hint
  assert.equal(hints.length, 1);
  assert.match(hints[0].textContent, /10 bonus points are waiting/);
  assert.match(hints[0].textContent, /Added once today's chores are done/);
});

test("a held bonus chore linked to a task is hidden just like an unlinked one", async () => {
  const vacuum = task("t1", "Vacuum", { labels: ["bonus"] });
  const open = bonusHass({ bonus_chores: { Vacuum: 5 }, pending: [], tasks: [vacuum] });
  assert.deepEqual(rowNames(await mount(win, "kid-chores-bonus-card", {}, open)), ["Vacuum"]);
  const held = bonusHass({ bonus_chores: { Vacuum: 5 }, pending: [{ name: "Vacuum", points: 5 }], tasks: [vacuum] });
  assert.deepEqual(rowNames(await mount(win, "kid-chores-bonus-card", {}, held)), []);
});

test("the bonus card shows the same encouragement once the mandatory chores are done", async () => {
  const hass = bonusHass({ bonus_chores: { Vacuum: 5 }, pending: [] });
  hass.states["sensor.kid_mandatory_remaining"].attributes.remaining = [];
  const card = await mount(win, "kid-chores-bonus-card", {}, hass);
  const banner = card.shadowRoot.querySelector(".bonus");
  assert.match(banner.textContent, /let's do a first bonus chore/);
  assert.match(banner.textContent, /added right away/);
});

test("once mandatory chores are done the banner shows the bonus points earned today", async () => {
  const hass = bonusHass({ bonus_chores: { Vacuum: 5, Weeds: 10 }, pending: [] });
  hass.states["sensor.kid_mandatory_remaining"].attributes.remaining = [];
  hass.states["sensor.kid_points_today"].attributes.bonus_done = ["Weeds"];
  const card = await mount(win, "kid-chores-bonus-card", {}, hass);
  assert.deepEqual(rowNames(card), ["Vacuum"]);
  const banner = card.shadowRoot.querySelector(".bonus");
  assert.match(banner.textContent, /10 bonus points earned today/);
  assert.match(banner.textContent, /Added to the bank/);
});

test("the bonus card encourages a first bonus chore, and only shows a hint when there is something to do or hold", async () => {
  const hint = async (bonus_chores) =>
    (await mount(win, "kid-chores-bonus-card", {}, bonusHass({ bonus_chores, pending: [] }))).shadowRoot.querySelector(".bonus");
  assert.match((await hint({ Vacuum: 5 })).textContent, /let's do a first bonus chore/);
  assert.equal(await hint({}), null);
  // held points are still reported when no bonus chore is left to show
  const held = bonusHass({ bonus_chores: { Weeds: 10 }, pending: [{ name: "Weeds", points: 10 }] });
  const card = await mount(win, "kid-chores-bonus-card", {}, held);
  assert.deepEqual(rowNames(card), []);
  assert.match(card.shadowRoot.querySelector(".bonus").textContent, /10 bonus points are waiting/);
});

const rowNames = (card) =>
  [...card.shadowRoot.querySelectorAll(".row .primary")].map((el) => el.textContent);

test("a chore is paired with its task by name", async () => {
  const hass = todoHass({
    remaining: ["Dishes"],
    chores: { Dishes: 20 },
    tasks: [task("t1", "Dishes")],
  });
  const card = await mount(win, "kid-chores-todo-card", {}, hass);
  assert.deepEqual(rowNames(card), ["Dishes"]);
  card.shadowRoot.querySelector(".btn").click();
  await new Promise((r) => setTimeout(r, 0));
  assert.deepEqual(hass.calls, [
    { domain: "maintenance_supporter", service: "complete", data: { entity_id: "sensor.ms_t1" } },
  ]);
});

test("a linked chore still gets its button after the task was renamed", async () => {
  const hass = todoHass({
    remaining: ["Dishes"],
    chores: { Dishes: 20 },
    ids: { Dishes: "t1" },
    tasks: [task("t1", "Wash the dishes")],
  });
  const card = await mount(win, "kid-chores-todo-card", {}, hass);
  // one row, under the chore's own name, not an extra row for the renamed task
  assert.deepEqual(rowNames(card), ["Dishes"]);
  assert.ok(card.shadowRoot.querySelector(".btn"));
});

test("without a link a renamed task shows up as a separate row", async () => {
  const hass = todoHass({
    remaining: ["Dishes"],
    chores: { Dishes: 20 },
    tasks: [task("t1", "Wash the dishes")],
  });
  const card = await mount(win, "kid-chores-todo-card", {}, hass);
  assert.deepEqual(rowNames(card).sort(), ["Dishes", "Wash the dishes"]);
});

test("the link wins over a task that happens to share the chore's name", async () => {
  const hass = todoHass({
    remaining: ["Dishes"],
    chores: { Dishes: 20 },
    ids: { Dishes: "t1" },
    tasks: [task("t1", "Wash the dishes"), task("t2", "Dishes")],
  });
  const card = await mount(win, "kid-chores-todo-card", {}, hass);
  card.shadowRoot.querySelector(".btn").click();
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(hass.calls[0].data.entity_id, "sensor.ms_t1");
});

test("a task outside the card's label filter hides its chore", async () => {
  const hass = todoHass({
    remaining: ["Dishes"],
    chores: { Dishes: 20 },
    ids: { Dishes: "t1" },
    tasks: [task("t1", "Wash the dishes", { labels: ["other"] })],
  });
  const card = await mount(win, "kid-chores-todo-card", {}, hass);
  assert.deepEqual(rowNames(card), []);
});

test("without a tracker the cards say so", async () => {
  const card = await mount(win, "kid-chores-todo-card", {}, makeHass());
  assert.match(card.shadowRoot.textContent, /No Kid Chores & Points tracker found/);
});

// ---------------------------------------------------------------------
// Rewards and wallet cards
// ---------------------------------------------------------------------
test("rewards card lists affordable rewards and redeems after confirming", async () => {
  const hass = makeHass();
  hass.states["binary_sensor.can_afford_tv"] = {
    state: "on",
    attributes: { reward: "TV time", cost: 10, bank: 25, payout: 0, currency: "kr", entry_id: "entry-1" },
  };
  hass.entities["binary_sensor.can_afford_tv"] = { platform: "kid_chores_points", device_id: "dev1" };
  const card = await mount(win, "kid-chores-rewards-card", {}, hass);
  assert.match(card.shadowRoot.textContent, /TV time/);
  card.shadowRoot.querySelector(".row[data-id]").click();
  card.shadowRoot.querySelector('[data-act="yes"]').click();
  assert.equal(hass.calls[0].service, "redeem");
});

test("wallet card shows the balance and recent movements", async () => {
  const history = [
    { t: "2026-10-21T10:00:00+00:00", type: "redeem", label: "Pocket money", amount: 50, points: -50 },
    { t: "2026-10-20T10:00:00+00:00", type: "adjust", target: "wallet", label: "Gift", amount: 20 },
  ];
  const hass = makeHass({
    sensors: {
      wallet: { state: "70", attributes: { currency: "kr" } },
      points_history: { state: "2", attributes: { history } },
    },
  });
  const card = await mount(win, "kid-chores-wallet-card", {}, hass);
  const text = card.shadowRoot.textContent;
  assert.match(text, /70 kr/);
  assert.match(text, /Pocket money/);
  assert.match(text, /Gift/);
});

// ---------------------------------------------------------------------
// Streaks and medals
// ---------------------------------------------------------------------
const today = () => new Date().toLocaleDateString("sv-SE"); // YYYY-MM-DD, local time

const medal = (id, extra = {}) => ({
  id,
  kind: "day",
  tier: "bronze",
  name: "Little Sprout",
  how: "Do all your daily chores 3 days in a row",
  at: 3,
  bonus: 5,
  earned: null,
  progress: 2,
  available: true,
  ...extra,
});

const medalsHass = (medals, { enabled = true, day = "2", week = "1" } = {}) =>
  makeHass({
    sensors: {
      medals: { state: String(medals.filter((m) => m.earned).length), attributes: { enabled, medals } },
      day_streak: { state: day, attributes: { enabled, best: 4, at_risk: false, next: null } },
      week_streak: { state: week, attributes: { enabled, best: 1, next: null } },
      wallet: { state: "0", attributes: { currency: "kr", enabled: false } },
    },
  });

test("medals card says how to switch the feature on when it is off", async () => {
  const card = await mount(win, "kid-chores-medals-card", {}, medalsHass([medal("day_3")], { enabled: false }));
  assert.match(card.shadowRoot.textContent, /switched off/);
  assert.equal(card.shadowRoot.querySelectorAll(".medal").length, 0);
});

test("medals card shows earned medals, and locked ones with what to do and how far along", async () => {
  const medals = [
    medal("day_3", { earned: "2026-01-05", progress: 3 }),
    medal("day_7", { name: "Super Seven", how: "Do all your daily chores 7 days in a row", at: 7, bonus: 10, progress: 2 }),
    medal("chores_25", { kind: "chores", name: "Broom Buddy", how: "Complete 25 chores", at: 25, progress: 10 }),
  ];
  const card = await mount(win, "kid-chores-medals-card", {}, medalsHass(medals));
  const root = card.shadowRoot;
  const got = root.querySelector('.medal[data-id="day_3"]');
  assert.ok(got.classList.contains("got"));
  assert.match(got.textContent, /Little Sprout/);
  assert.match(got.textContent, /Earned Jan 5/);
  assert.ok(got.querySelector("svg"));

  const locked = root.querySelector('.medal[data-id="day_7"]');
  assert.ok(locked.classList.contains("lock"));
  assert.match(locked.textContent, /Do all your daily chores 7 days in a row/);
  assert.match(locked.textContent, /2 \/ 7 days/);
  assert.match(locked.textContent, /\+10 p/);
  assert.equal(locked.querySelector(".bar div").style.width, "29%");

  assert.match(root.querySelector('.medal[data-id="chores_25"]').textContent, /10 \/ 25 chores/);
  assert.match(root.textContent, /1 of 3 medals/);
  assert.match(root.textContent, /2 days/); // the day streak chip
  assert.equal(root.querySelectorAll(".sec").length, 2); // Streaks and Chores; no bonus or wallet medals
});

test("medals that don't apply to this setup are hidden until earned", async () => {
  const medals = [
    medal("day_3"),
    medal("bonus_10", { kind: "bonus", name: "Dino Egg", at: 10, bonus: 5, available: false }),
    medal("first_treat", { kind: "treat", tier: "treat", name: "Treat Yourself!", at: 1, bonus: 0, available: true, earned: "2026-01-05", progress: 1 }),
  ];
  const card = await mount(win, "kid-chores-medals-card", {}, medalsHass(medals));
  const ids = Array.from(card.shadowRoot.querySelectorAll(".medal"), (el) => el.dataset.id);
  assert.deepEqual(ids, ["day_3", "first_treat"]);
});

test("a medal earned in the last days is marked new, an older one is not", async () => {
  const medals = [medal("day_3", { earned: today() }), medal("day_7", { earned: "2026-01-05", at: 7 })];
  const card = await mount(win, "kid-chores-medals-card", {}, medalsHass(medals));
  assert.ok(card.shadowRoot.querySelector('.medal[data-id="day_3"] .new'));
  assert.equal(card.shadowRoot.querySelector('.medal[data-id="day_7"] .new'), null);
});

test("medals card follows the user's language", async () => {
  const hass = medalsHass([medal("day_3", { name: "Lilla Grodden", earned: "2026-01-05" })]);
  hass.language = "sv";
  const card = await mount(win, "kid-chores-medals-card", {}, hass);
  assert.match(card.shadowRoot.textContent, /1 av 1 medaljer/);
  assert.match(card.shadowRoot.textContent, /Serier/);
});

test("every medal has an icon, and two renders never share gradient ids", () => {
  const ids = [
    "day_3", "day_7", "day_14", "day_30", "week_10", "week_12", "week_16", "week_20",
    "chores_25", "chores_100", "chores_250", "chores_500", "chores_1000", "first_treat",
    "bonus_10", "bonus_50", "bonus_100", "bonus_250",
  ]; // prettier-ignore
  const holder = win.document.createElement("div");
  win.document.body.appendChild(holder);
  const card = win.document.createElement("kid-chores-medals-card");
  card.setConfig({});
  card.hass = medalsHass(ids.map((id) => medal(id, { kind: "day", earned: "2026-01-05" })));
  holder.appendChild(card);
  const svgs = card.shadowRoot.querySelectorAll(".medal svg");
  assert.equal(svgs.length, ids.length);
  const gradients = Array.from(card.shadowRoot.querySelectorAll("linearGradient, radialGradient"), (g) => g.id);
  assert.equal(new Set(gradients).size, gradients.length);
  assert.ok(gradients.every((id) => !id.includes("__")));
});

test("status card shows one streak tile: the day streak when its medal is nearest", async () => {
  const hass = medalsHass([], { day: "5", week: "3" });
  hass.states["sensor.kid_day_streak"].attributes.next = { id: "day_7", name: "Super Seven", at: 7, remaining: 2 };
  hass.states["sensor.kid_week_streak"].attributes.next = { id: "week_10", name: "Bullseye!", at: 10, remaining: 7 };
  const card = await mount(win, "kid-chores-status-card", {}, hass);
  const text = card.shadowRoot.textContent;
  assert.match(text, /5 days/);
  assert.match(text, /2 more for “Super Seven”/);
  assert.doesNotMatch(text, /3 weeks/);
  assert.doesNotMatch(text, /Bullseye/);
  assert.doesNotMatch(text, /Finish today's chores/);
});

test("the streak tile switches to the week streak when that medal is nearer", async () => {
  const hass = medalsHass([], { day: "20", week: "9" });
  hass.states["sensor.kid_day_streak"].attributes.next = { id: "day_30", name: "Unstoppable!", at: 30, remaining: 10 };
  hass.states["sensor.kid_week_streak"].attributes.next = { id: "week_10", name: "Bullseye!", at: 10, remaining: 1 };
  const card = await mount(win, "kid-chores-status-card", {}, hass);
  const text = card.shadowRoot.textContent;
  assert.match(text, /9 weeks/);
  assert.match(text, /1 more for “Bullseye!”/);
  assert.doesNotMatch(text, /20 days/);
});

test("the streak tile warns when the day streak is at risk, and shows the best streak when every medal is earned", async () => {
  const hass = medalsHass([], { day: "5", week: "3" });
  hass.states["sensor.kid_day_streak"].attributes.next = { id: "day_7", name: "Super Seven", at: 7, remaining: 2 };
  hass.states["sensor.kid_day_streak"].attributes.at_risk = true;
  const card = await mount(win, "kid-chores-status-card", {}, hass);
  assert.match(card.shadowRoot.textContent, /Finish today's chores to keep your 5-day streak!/);
  assert.match(card.shadowRoot.textContent, /2 more for “Super Seven”/);

  hass.states["sensor.kid_day_streak"].attributes = { enabled: true, key: "day_streak", best: 40, at_risk: false, next: null };
  hass.states["sensor.kid_day_streak"].state = "6";
  card.hass = { ...hass };
  assert.match(card.shadowRoot.textContent, /6 days/);
  assert.match(card.shadowRoot.textContent, /Best: 40/);
  assert.doesNotMatch(card.shadowRoot.textContent, /Finish today's chores/);
});

test("status card shows no streak tiles while the feature is off", async () => {
  const card = await mount(win, "kid-chores-status-card", {}, medalsHass([], { enabled: false }));
  assert.doesNotMatch(card.shadowRoot.textContent, /streak/i);
});

test("a medal in the history card shows its bonus, or nothing for an honorary one", async () => {
  const history = [
    entry({ id: "m2", group: "g", can_revert: false, type: "medal", label: "Cha-Ching!", points: 0, target: "bank" }),
    entry({ id: "m1", group: "g", can_revert: false, type: "medal", label: "Little Sprout", points: 5, target: "bank" }),
  ];
  const card = await mount(win, "kid-chores-history-card", {}, historyHass(history));
  const rows = card.shadowRoot.querySelectorAll(".row");
  assert.match(rows[0].textContent, /Cha-Ching!/);
  assert.match(rows[0].textContent, /Medal earned/);
  assert.doesNotMatch(rows[0].querySelector(".pts").textContent, /\d/);
  assert.match(rows[1].querySelector(".pts").textContent, /\+5 p to the bank/);
});

test("medals card shows every medal, earned or not", async () => {
  const medals = [
    medal("day_3", { earned: "2026-01-05", progress: 3 }),
    medal("day_7", { name: "Super Seven", at: 7, progress: 5 }),
    medal("day_14", { name: "Hot Streak", at: 14, progress: 5 }),
    medal("week_10", { kind: "week", name: "Bullseye!", at: 10, progress: 3 }),
    medal("week_12", { kind: "week", name: "Goal-o-Matic", at: 12, progress: 3 }),
  ];
  const card = await mount(win, "kid-chores-medals-card", {}, medalsHass(medals));
  const ids = Array.from(card.shadowRoot.querySelectorAll(".medal"), (el) => el.dataset.id);
  assert.deepEqual(ids, ["day_3", "day_7", "day_14", "week_10", "week_12"]);
  assert.equal(card.shadowRoot.querySelector(".more"), null);
});

test("medal names and texts come in the viewer's language, whatever language the server runs in", async () => {
  const names = { en: "Little Sprout", sv: "Lilla Grodden" };
  const hows = { en: "Do all your daily chores 3 days in a row", sv: "Gör alla dagens sysslor 3 dagar i rad" };
  const hass = medalsHass([medal("day_3", { names, hows })]); // name and how are in English
  hass.language = "sv";
  hass.states["sensor.kid_day_streak"].attributes.next = {
    id: "day_3", name: "Little Sprout", names, at: 3, remaining: 1,
  };
  const card = await mount(win, "kid-chores-medals-card", {}, hass);
  assert.match(card.shadowRoot.textContent, /Lilla Grodden/);
  assert.match(card.shadowRoot.textContent, /Gör alla dagens sysslor 3 dagar i rad/);
  assert.doesNotMatch(card.shadowRoot.textContent, /Little Sprout/);

  const status = await mount(win, "kid-chores-status-card", {}, hass);
  assert.match(status.shadowRoot.textContent, /1 till ”Lilla Grodden”/);
});
