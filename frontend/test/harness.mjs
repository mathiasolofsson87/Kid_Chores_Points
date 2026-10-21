// Loads the built bundle into a jsdom window, the way the browser loads it.
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const BUNDLE = new URL(
  "../../custom_components/kid_chores_points/www/kid-chores-cards.js",
  import.meta.url,
);

export function loadCards() {
  const dom = new JSDOM("<!doctype html><body></body>", { runScripts: "outside-only" });
  dom.window.eval(readFileSync(BUNDLE, "utf8"));
  return dom.window;
}

const sensor = (key, attributes = {}, state = "0") => ({
  state,
  last_updated: "2026-10-21T12:00:00Z",
  attributes: { key, entry_id: "entry-1", ...attributes },
});

/** A fake `hass` with one tracker (sensors by key) and optional Maintenance Supporter tasks. */
export function makeHass({ sensors = {}, objects = [], language = "en" } = {}) {
  const states = {};
  const entities = {};
  for (const [key, st] of Object.entries(sensors)) {
    const id = `sensor.kid_${key}`;
    states[id] = sensor(key, st.attributes, st.state);
    entities[id] = { platform: "kid_chores_points", device_id: "dev1" };
  }
  const calls = [];
  return {
    language,
    states,
    entities,
    calls,
    connection: { sendMessagePromise: async () => ({ objects }) },
    // plain objects: the cards run in the jsdom realm, whose Object differs from Node's
    callService: async (domain, service, data) =>
      calls.push(JSON.parse(JSON.stringify({ domain, service, data }))),
  };
}

export const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

/** Create a card element, give it a config and a hass, and wait for async work. */
export async function mount(win, tag, config, hass) {
  const card = win.document.createElement(tag);
  win.document.body.appendChild(card);
  card.setConfig(config);
  card.hass = hass;
  await tick();
  return card;
}
