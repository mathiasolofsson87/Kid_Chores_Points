import assert from "node:assert/strict";
import { test } from "node:test";

import { loadCards, makeHass, mount } from "./harness.mjs";

const win = loadCards();

const CARDS = ["rewards", "status", "adjust", "history", "todo", "bonus", "wallet"];

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
