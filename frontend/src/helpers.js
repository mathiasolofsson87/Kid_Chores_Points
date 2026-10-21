/* Shared helpers for the cards. */
import { KCP_TEXT } from "./text.js";

// the card picker reads this list; every card module adds itself to it
window.customCards = window.customCards || [];

const KCP_ICONS = [
  [/xbox/, "mdi:microsoft-xbox"],
  [/playstation|\bps[2-5]\b/, "mdi:sony-playstation"],
  [/nintendo|switch/, "mdi:nintendo-switch"],
  [/screen|skärm|tablet|ipad|phone|mobil|surfplatta/, "mdi:tablet-cellphone"],
  [/\bkr\b|money|cash|pengar|veckopeng|\$|€|sek|usd/, "mdi:cash"],
  [/game|spel|gaming|dator|computer|pc\b/, "mdi:controller"],
  [/\btv\b|film|movie|netflix|youtube/, "mdi:television-play"],
  [/candy|godis|snack|glass|ice ?cream|chocolate|choklad/, "mdi:candy"],
  [/sleep|sova|bedtime|läggdags/, "mdi:sleep"],
];

export const kcpIcon = (name) => {
  const n = name.toLowerCase();
  for (const [re, icon] of KCP_ICONS) if (re.test(n)) return icon;
  return "mdi:gift";
};

export const kcpEsc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export const kcpT = (hass, key, vars = {}) => {
  const lang = (hass?.language || "en").slice(0, 2);
  let s = (KCP_TEXT[lang] || KCP_TEXT.en)[key];
  for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, v);
  return s;
};

/* Sensors of one tracker, by their "key" attribute. Picks `device`, or the
 * first tracker found when none is configured. */
export const kcpSensors = (hass, device) => {
  const found = [];
  for (const [id, st] of Object.entries(hass.states)) {
    if (!id.startsWith("sensor.")) continue;
    const reg = hass.entities?.[id];
    if (reg?.platform !== "kid_chores_points" || st.attributes.key === undefined) continue;
    found.push({ st, device: reg.device_id });
  }
  if (!found.length) return null;
  const chosen = device || found.map((f) => f.device).sort()[0];
  const out = { _device: chosen };
  for (const f of found) if (f.device === chosen) out[f.st.attributes.key] = f.st;
  return out;
};
