/* Kid Chores & Points – dashboard cards (rewards + status).
 * Served by the integration and auto-loaded on every dashboard.
 * Add via: Edit dashboard -> Add card -> "Kid Chores & Points – ...".
 */
const KCP_TEXT = {
  en: {
    title: "Redeem points",
    subtitle: "You have {n} points in the bank",
    confirm: "Redeem {r}?",
    yes: "Redeem",
    no: "Cancel",
    points: "points",
    collect: "Collect more points!",
    short: "{n} more points needed",
    none: "No rewards configured yet. Add some under Configure → Rewards.",
    no_tracker: "No Kid Chores & Points tracker found.",
    chores: "Chores",
    goal_line: "🎯 Goal for the week: {n} points",
    progress: "Towards the weekly goal",
    this_week: "This week",
    to_goal: "Left to goal",
    today: "Today",
    bank: "Points bank",
    last_week: "Last week",
    adjust_title: "Adjust points",
    adjust_target: "Adjust",
    t_bank: "Bank",
    t_week: "This week",
    adjust_points: "Points (use - to deduct)",
    adjust_reason: "Reason (optional)",
    apply: "Apply",
    invalid: "Enter a whole number, e.g. 5 or -5",
    added: "Added {n} to {t}",
    deducted: "Deducted {n} from {t}",
    failed: "Failed: {e}",
  },
  sv: {
    title: "Lös in poäng",
    subtitle: "Du har {n} poäng i banken",
    confirm: "Lös in {r}?",
    yes: "Lös in",
    no: "Avbryt",
    points: "poäng",
    collect: "Samla fler poäng!",
    short: "{n} poäng kvar",
    none: "Inga belöningar inställda än. Lägg till under Konfigurera → Rewards.",
    no_tracker: "Ingen Kid Chores & Points-tracker hittades.",
    chores: "Sysslor",
    goal_line: "🎯 Mål för veckan: {n} poäng",
    progress: "Mot veckomålet",
    this_week: "Denna vecka",
    to_goal: "Kvar till målet",
    today: "Idag",
    bank: "Poängbanken",
    last_week: "Förra veckan",
    adjust_title: "Justera poäng",
    adjust_target: "Justera",
    t_bank: "Banken",
    t_week: "Veckan",
    adjust_points: "Poäng (använd - för avdrag)",
    adjust_reason: "Anledning (valfritt)",
    apply: "Verkställ",
    invalid: "Ange ett heltal, t.ex. 5 eller -5",
    added: "Lade till {n} i {t}",
    deducted: "Drog av {n} från {t}",
    failed: "Misslyckades: {e}",
  },
};

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

const kcpIcon = (name) => {
  const n = name.toLowerCase();
  for (const [re, icon] of KCP_ICONS) if (re.test(n)) return icon;
  return "mdi:gift";
};

const kcpEsc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const kcpT = (hass, key, vars = {}) => {
  const lang = (hass?.language || "en").slice(0, 2);
  let s = (KCP_TEXT[lang] || KCP_TEXT.en)[key];
  for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, v);
  return s;
};

/* Sensors of one tracker, by their "key" attribute. Picks `device`, or the
 * first tracker found when none is configured. */
const kcpSensors = (hass, device) => {
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

class KidChoresRewardsCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._confirm = null; // entity_id awaiting confirmation
    this._sig = "";
  }

  static getConfigElement() {
    return document.createElement("kid-chores-rewards-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = { show_unaffordable: false, show_hint: true, color: "#30d158", ...config };
    this._sig = "";
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 1 + (this._rewards ? this._rewards.length : 3);
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  _t(key, vars = {}) {
    const lang = (this._hass?.language || "en").slice(0, 2);
    let s = (KCP_TEXT[lang] || KCP_TEXT.en)[key];
    for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, v);
    return s;
  }

  _findRewards() {
    const h = this._hass;
    const found = [];
    for (const [id, st] of Object.entries(h.states)) {
      if (!id.startsWith("binary_sensor.")) continue;
      const reg = h.entities?.[id];
      if (reg?.platform !== "kid_chores_points") continue;
      if (st.attributes.reward === undefined) continue;
      found.push({ id, st, device: reg.device_id });
    }
    if (!found.length) return [];
    const device = this._config.device || found.map((f) => f.device).sort()[0];
    return found
      .filter((f) => f.device === device)
      .sort((a, b) => a.st.attributes.cost - b.st.attributes.cost);
  }

  _render() {
    if (!this._hass || !this._config) return;
    const rewards = this._findRewards();
    this._rewards = rewards;
    const sig = JSON.stringify([
      rewards.map((r) => [r.id, r.st.state, r.st.attributes.cost, r.st.attributes.bank, r.st.attributes.reward]),
      this._confirm,
      this._hass.language,
      this._config,
    ]);
    if (sig === this._sig) return;
    this._sig = sig;

    const color = this._config.color;
    const icons = this._config.icons || {};
    const bank = rewards.length ? rewards[0].st.attributes.bank : 0;
    const title = this._config.title ?? this._t("title");
    const anyAffordable = rewards.some((r) => r.st.state === "on");

    let body = "";
    if (!rewards.length) {
      const hasTracker = Object.keys(this._hass.entities || {}).some(
        (e) => this._hass.entities[e].platform === "kid_chores_points"
      );
      body = `<div class="empty">${this._t(hasTracker ? "none" : "no_tracker")}</div>`;
    }

    for (const r of rewards) {
      const a = r.st.attributes;
      const affordable = r.st.state === "on";
      if (!affordable && !this._config.show_unaffordable) continue;
      const icon = icons[a.reward] || kcpIcon(a.reward);
      const asking = this._confirm === r.id;
      body += `
        <div class="row ${affordable ? "" : "locked"}" data-id="${kcpEsc(r.id)}" style="--c:${affordable ? color : "var(--disabled-text-color, #9e9e9e)"}">
          <div class="ico"><ha-icon icon="${kcpEsc(icon)}"></ha-icon></div>
          <div class="txt">
            <div class="primary">${kcpEsc(a.reward)}</div>
            <div class="secondary">${
              asking
                ? kcpEsc(this._t("confirm", { r: a.reward }))
                : affordable
                ? `${a.cost} ${this._t("points")}`
                : `${a.cost} ${this._t("points")} · ${this._t("short", { n: a.cost - a.bank })}`
            }</div>
          </div>
          ${
            asking
              ? `<div class="btns"><button class="yes" data-act="yes">${this._t("yes")}</button><button class="no" data-act="no">${this._t("no")}</button></div>`
              : ""
          }
        </div>`;
    }

    if (rewards.length && !anyAffordable && this._config.show_hint !== false) {
      const costs = rewards.map((r) => kcpEsc(`${r.st.attributes.reward} = ${r.st.attributes.cost} p`)).join("<br>");
      body += `
        <div class="row hint" style="--c:var(--disabled-text-color, #9e9e9e)">
          <div class="ico"><ha-icon icon="mdi:arm-flex"></ha-icon></div>
          <div class="txt"><div class="primary">${this._t("collect")}</div><div class="secondary">${costs}</div></div>
        </div>`;
    }

    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .head .t { font-size: 1.4em; font-weight: 600; color: var(--primary-text-color); }
        .head .s { color: var(--secondary-text-color); margin-top: 2px; }
        .list { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
        .row { display: flex; align-items: center; gap: 12px; padding: 10px 12px;
          background: var(--secondary-background-color, rgba(127,127,127,.1));
          border-left: 4px solid var(--c); border-radius: 12px; }
        .row:not(.locked):not(.hint) { cursor: pointer; }
        .row.locked { opacity: .6; }
        .ico { width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center;
          flex: none; color: var(--c); background: color-mix(in srgb, var(--c) 20%, transparent); }
        .txt { flex: 1; min-width: 0; }
        .primary { font-weight: 500; color: var(--primary-text-color); }
        .secondary { font-size: .9em; color: var(--secondary-text-color); white-space: normal; }
        .btns { display: flex; gap: 6px; flex: none; }
        button { border: 0; border-radius: 8px; padding: 8px 12px; font: inherit; cursor: pointer; }
        .yes { background: var(--c); color: #fff; }
        .no { background: transparent; color: var(--secondary-text-color); }
        .empty { color: var(--secondary-text-color); padding: 12px 0; }
      </style>
      <ha-card>
        <div class="head">
          <div class="t">${kcpEsc(title)}</div>
          ${rewards.length ? `<div class="s">${this._t("subtitle", { n: bank })}</div>` : ""}
        </div>
        <div class="list">${body}</div>
      </ha-card>`;

    this.shadowRoot.querySelectorAll(".row[data-id]").forEach((el) => {
      el.addEventListener("click", (ev) => {
        const id = el.dataset.id;
        const act = ev.target.closest("button")?.dataset.act;
        const reward = this._rewards.find((r) => r.id === id);
        if (!reward) return;
        if (act === "yes") {
          this._confirm = null;
          this._hass.callService("kid_chores_points", "redeem", {
            reward: reward.st.attributes.reward,
            units: 1,
            config_entry: reward.st.attributes.entry_id,
          });
        } else if (act === "no") {
          this._confirm = null;
        } else if (reward.st.state === "on") {
          this._confirm = id;
        }
        this._sig = "";
        this._render();
      });
    });
  }
}

class KidChoresRewardsCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
    else this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) =>
        ({ device: "Tracker (leave empty for the first one)", title: "Title", show_unaffordable: "Also show rewards that can't be afforded yet", show_hint: "Show the \"collect more points\" hint when nothing is affordable", color: "Accent colour" }[s.name] || s.name);
      this._form.schema = [
        { name: "device", selector: { device: { integration: "kid_chores_points" } } },
        { name: "title", selector: { text: {} } },
        { name: "show_unaffordable", selector: { boolean: {} } },
        { name: "show_hint", selector: { boolean: {} } },
        { name: "color", selector: { text: {} } },
      ];
      this._form.addEventListener("value-changed", (ev) => {
        const config = { type: this._config.type, ...ev.detail.value };
        for (const k of Object.keys(config)) if (config[k] === "" || config[k] === undefined) delete config[k];
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = { show_unaffordable: false, show_hint: true, ...this._config };
  }
}

customElements.define("kid-chores-rewards-card", KidChoresRewardsCard);
customElements.define("kid-chores-rewards-card-editor", KidChoresRewardsCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kid-chores-rewards-card",
  name: "Kid Chores & Points – Rewards",
  description: "Shows the rewards configured in Kid Chores & Points and lets the child redeem them.",
  preview: true,
});


/* ------------------------------------------------------------------ */
/*  Status card                                                        */
/* ------------------------------------------------------------------ */
class KidChoresStatusCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._sig = "";
  }

  static getConfigElement() {
    return document.createElement("kid-chores-status-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = config;
    this._sig = "";
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  _chips() {
    const uid = this._hass.user?.id;
    return (this._config.chips || []).filter((c) => !c.users || c.users.includes(uid));
  }

  _render() {
    if (!this._hass || !this._config) return;
    const h = this._hass;
    const S = kcpSensors(h, this._config.device);
    const val = (k) => (S && S[k] ? S[k].state : undefined);
    const chips = this._chips();
    const sig = JSON.stringify([
      S && Object.entries(S).map(([k, v]) => (k === "_device" ? v : [k, v.state])),
      h.language,
      this._config,
      chips,
    ]);
    if (sig === this._sig) return;
    this._sig = sig;

    if (!S) {
      this.shadowRoot.innerHTML = `<ha-card style="padding:16px">${kcpT(h, "no_tracker")}</ha-card>`;
      return;
    }

    const n = (k) => parseInt(val(k), 10) || 0;
    const pct = Math.max(0, Math.min(100, n("week_progress")));
    const barColor = pct >= 100 ? "#30d158" : pct >= 50 ? "#ffd60a" : "#ff453a";
    const last = val("last_week_result");
    const showLast = last && !["unknown", "unavailable", ""].includes(last);
    const title = this._config.title ?? kcpT(h, "chores");
    const tile = (icon, color, primary, secondary) => `
      <div class="tile" style="--c:${color}">
        <div class="ico"><ha-icon icon="${icon}"></ha-icon></div>
        <div class="txt"><div class="primary">${kcpEsc(primary)}</div><div class="secondary">${kcpEsc(secondary)}</div></div>
      </div>`;

    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .t { font-size: 1.4em; font-weight: 600; color: var(--primary-text-color); }
        .s { color: var(--secondary-text-color); margin-top: 2px; }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .chip { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; cursor: pointer;
          border-radius: 18px; background: var(--secondary-background-color, rgba(127,127,127,.1));
          color: var(--primary-text-color); font-size: .9em; --mdc-icon-size: 18px; }
        .bar { margin-top: 16px; }
        .bar .lbl { display: flex; justify-content: space-between; color: var(--secondary-text-color); font-size: .9em; margin-bottom: 6px; }
        .track { height: 14px; border-radius: 7px; background: var(--secondary-background-color, rgba(127,127,127,.2)); overflow: hidden; }
        .fill { height: 100%; border-radius: 7px; transition: width .4s; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 16px; }
        .tile, .wide { display: flex; align-items: center; gap: 12px; padding: 10px 12px;
          background: var(--secondary-background-color, rgba(127,127,127,.1));
          border-left: 4px solid var(--c); border-radius: 12px; min-width: 0; }
        .wide { grid-column: 1 / -1; }
        .ico { width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; flex: none;
          color: var(--c); background: color-mix(in srgb, var(--c) 20%, transparent); }
        .txt { min-width: 0; }
        .primary { font-weight: 600; color: var(--primary-text-color); }
        .secondary { font-size: .9em; color: var(--secondary-text-color); }
      </style>
      <ha-card>
        <div class="t">${kcpEsc(title)}</div>
        <div class="s">${kcpEsc(kcpT(h, "goal_line", { n: n("weekly_goal") }))}</div>
        ${
          chips.length
            ? `<div class="chips">${chips
                .map(
                  (c, i) =>
                    `<span class="chip" data-i="${i}">${c.icon ? `<ha-icon icon="${kcpEsc(c.icon)}"></ha-icon>` : ""}${kcpEsc(c.label || "")}</span>`
                )
                .join("")}</div>`
            : ""
        }
        <div class="bar">
          <div class="lbl"><span>${kcpEsc(kcpT(h, "progress"))}</span><span>${pct}%</span></div>
          <div class="track"><div class="fill" style="width:${pct}%;background:${barColor}"></div></div>
        </div>
        <div class="grid">
          ${tile("mdi:star", "#ffd60a", `${n("points_week")} p`, kcpT(h, "this_week"))}
          ${tile("mdi:flag-variant", "#0a84ff", `${n("points_to_goal")} p`, kcpT(h, "to_goal"))}
          ${tile("mdi:calendar-check", "#30d158", `${n("points_today")} p`, kcpT(h, "today"))}
          ${tile("mdi:piggy-bank", "#ff9f0a", `${n("points_bank")} p`, kcpT(h, "bank"))}
          ${
            showLast
              ? `<div class="wide" style="--c:var(--disabled-text-color,#9e9e9e)">
                  <div class="ico"><ha-icon icon="mdi:history"></ha-icon></div>
                  <div class="txt"><div class="primary">${kcpEsc(kcpT(h, "last_week"))}</div><div class="secondary">${kcpEsc(last)}</div></div>
                </div>`
              : ""
          }
        </div>
      </ha-card>`;

    this.shadowRoot.querySelectorAll(".chip").forEach((el) => {
      el.addEventListener("click", () => {
        const chip = chips[Number(el.dataset.i)];
        if (!chip?.navigation_path) return;
        history.pushState(null, "", chip.navigation_path);
        window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
      });
    });
  }
}

class KidChoresStatusCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
    else this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) =>
        ({ device: "Tracker (leave empty for the first one)", title: "Title" }[s.name] || s.name);
      this._form.schema = [
        { name: "device", selector: { device: { integration: "kid_chores_points" } } },
        { name: "title", selector: { text: {} } },
      ];
      this._form.addEventListener("value-changed", (ev) => {
        const config = { ...this._config, ...ev.detail.value };
        for (const k of ["device", "title"]) if (config[k] === "" || config[k] === undefined) delete config[k];
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = { ...this._config };
  }
}

customElements.define("kid-chores-status-card", KidChoresStatusCard);
customElements.define("kid-chores-status-card-editor", KidChoresStatusCardEditor);
window.customCards.push({
  type: "kid-chores-status-card",
  name: "Kid Chores & Points – Status",
  description: "Weekly progress, points this week/today, bank balance and last week's result for one child.",
  preview: true,
});


/* ------------------------------------------------------------------ */
/*  Adjust points card (parents)                                       */
/* ------------------------------------------------------------------ */
class KidChoresAdjustCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._target = "bank";
    this._built = false;
  }

  static getConfigElement() {
    return document.createElement("kid-chores-adjust-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = config;
    this._update();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) this._build();
    this._update();
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  _build() {
    this._built = true;
    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .t { font-size: 1.4em; font-weight: 600; color: var(--primary-text-color); }
        .stats { display: flex; gap: 16px; margin-top: 4px; color: var(--secondary-text-color); }
        .stats b { color: var(--primary-text-color); }
        label { display: block; margin: 14px 0 6px; font-size: .9em; color: var(--secondary-text-color); }
        .seg { display: flex; border-radius: 10px; overflow: hidden; border: 1px solid var(--divider-color, #888); }
        .seg button { flex: 1; border: 0; padding: 10px; font: inherit; cursor: pointer;
          background: transparent; color: var(--primary-text-color); }
        .seg button.on { background: var(--primary-color); color: var(--text-primary-color, #fff); }
        input { width: 100%; box-sizing: border-box; padding: 12px; font: inherit; border-radius: 10px;
          border: 1px solid var(--divider-color, #888); background: var(--card-background-color);
          color: var(--primary-text-color); }
        input.num { font-size: 1.4em; text-align: center; }
        .apply { width: 100%; margin-top: 16px; padding: 12px; border: 0; border-radius: 10px; font: inherit;
          font-weight: 600; cursor: pointer; background: var(--primary-color); color: var(--text-primary-color, #fff); }
        .apply:disabled { opacity: .5; cursor: default; }
        .msg { margin-top: 10px; min-height: 1.2em; font-size: .9em; color: var(--secondary-text-color); }
        .msg.err { color: var(--error-color, #db4437); }
      </style>
      <ha-card>
        <div class="t"></div>
        <div class="stats"><span class="sw"></span><span class="sb"></span></div>
        <label class="l-target"></label>
        <div class="seg"><button data-t="bank"></button><button data-t="week"></button></div>
        <label class="l-points"></label>
        <input class="num" type="text" inputmode="text" autocomplete="off" placeholder="5 / -5" />
        <label class="l-reason"></label>
        <input class="reason" type="text" autocomplete="off" />
        <button class="apply"></button>
        <div class="msg"></div>
      </ha-card>`;
    const $ = (q) => this.shadowRoot.querySelector(q);
    this._el = {
      title: $(".t"), sw: $(".sw"), sb: $(".sb"),
      lTarget: $(".l-target"), lPoints: $(".l-points"), lReason: $(".l-reason"),
      num: $(".num"), reason: $(".reason"), apply: $(".apply"), msg: $(".msg"),
      bankBtn: $('[data-t="bank"]'), weekBtn: $('[data-t="week"]'),
    };
    for (const b of [this._el.bankBtn, this._el.weekBtn]) {
      b.addEventListener("click", () => {
        this._target = b.dataset.t;
        this._update();
      });
    }
    this._el.apply.addEventListener("click", () => this._apply());
    this._el.num.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") this._apply();
    });
  }

  _update() {
    if (!this._built || !this._hass || !this._config) return;
    const h = this._hass, e = this._el;
    const S = kcpSensors(h, this._config.device);
    e.title.textContent = this._config.title ?? kcpT(h, "adjust_title");
    e.lTarget.textContent = kcpT(h, "adjust_target");
    e.lPoints.textContent = kcpT(h, "adjust_points");
    e.lReason.textContent = kcpT(h, "adjust_reason");
    e.apply.textContent = kcpT(h, "apply");
    e.bankBtn.textContent = kcpT(h, "t_bank");
    e.weekBtn.textContent = kcpT(h, "t_week");
    e.bankBtn.classList.toggle("on", this._target === "bank");
    e.weekBtn.classList.toggle("on", this._target === "week");
    e.apply.disabled = !S;
    if (!S) {
      e.msg.textContent = kcpT(h, "no_tracker");
      e.msg.classList.add("err");
      e.sw.textContent = e.sb.textContent = "";
      return;
    }
    e.sw.innerHTML = `${kcpEsc(kcpT(h, "this_week"))}: <b>${parseInt(S.points_week?.state, 10) || 0} p</b>`;
    e.sb.innerHTML = `${kcpEsc(kcpT(h, "bank"))}: <b>${parseInt(S.points_bank?.state, 10) || 0} p</b>`;
  }

  _say(text, err = false) {
    this._el.msg.textContent = text;
    this._el.msg.classList.toggle("err", err);
  }

  async _apply() {
    const h = this._hass, e = this._el;
    const S = kcpSensors(h, this._config.device);
    if (!S) return;
    const raw = e.num.value.trim().replace(/[\u2212\u2013]/g, "-");
    if (!/^[+-]?\d+$/.test(raw) || parseInt(raw, 10) === 0) {
      this._say(kcpT(h, "invalid"), true);
      return;
    }
    const points = parseInt(raw, 10);
    const data = {
      target: this._target,
      points,
      config_entry: (S.points_bank || S.points_week).attributes.entry_id,
    };
    const reason = e.reason.value.trim();
    if (reason) data.reason = reason;
    e.apply.disabled = true;
    try {
      await h.callService("kid_chores_points", "adjust_points", data);
      const t = kcpT(h, this._target === "bank" ? "t_bank" : "t_week");
      this._say(kcpT(h, points > 0 ? "added" : "deducted", { n: Math.abs(points), t }));
      e.num.value = "";
      e.reason.value = "";
    } catch (err) {
      this._say(kcpT(h, "failed", { e: err?.message || err }), true);
    }
    e.apply.disabled = false;
  }
}

class KidChoresAdjustCardEditor extends KidChoresStatusCardEditor {}

customElements.define("kid-chores-adjust-card", KidChoresAdjustCard);
customElements.define("kid-chores-adjust-card-editor", KidChoresAdjustCardEditor);
window.customCards.push({
  type: "kid-chores-adjust-card",
  name: "Kid Chores & Points – Adjust points",
  description: "Parent tool: add or deduct points in the bank or this week.",
  preview: true,
});
