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
    history_title: "Points history",
    h_empty: "No history yet.",
    h_chore: "Chore",
    h_bonus: "Bonus chore",
    h_bonus_released: "Bonus released",
    h_pending: "Bonus waiting",
    h_redeem: "Redeemed",
    h_adjust: "Adjustment",
    h_week_close: "Week closed",
    h_no_reason: "No reason given",
    h_to_bank: "to the bank",
    h_balances: "Week {w} · Bank {b}",
    h_today: "Today",
    h_yesterday: "Yesterday",
    h_more: "Show more",
    todo_title: "Must do today",
    todo_done: "🎉 All done for today – great job!",
    todo_btn: "Done",
    todo_overdue: "Overdue",
    todo_due: "Due today",
    todo_failed: "Could not complete: {e}",
    bonus_title: "Bonus chores",
    bonus_locked: "🔒 Bonus chores unlock when today's chores are done.",
    bonus_pending: "⏳ {n} bonus points are waiting to be added!",
    bonus_none: "No bonus chores configured yet.",
    wallet_title: "Wallet",
    wallet_sub: "Money you have saved",
    t_wallet: "Wallet",
    adjust_amount: "Amount (use - to deduct)",
    w_recent: "Recent activity",
    w_empty: "No money yet. Cash out points to fill your wallet!",
    h_cashout: "Cashed out",
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
    history_title: "Poänghistorik",
    h_empty: "Ingen historik än.",
    h_chore: "Syssla",
    h_bonus: "Bonussyssla",
    h_bonus_released: "Bonus utbetald",
    h_pending: "Bonus väntar",
    h_redeem: "Inlöst",
    h_adjust: "Justering",
    h_week_close: "Veckan stängd",
    h_no_reason: "Ingen anledning angiven",
    h_to_bank: "till banken",
    h_balances: "Vecka {w} · Bank {b}",
    h_today: "Idag",
    h_yesterday: "Igår",
    h_more: "Visa fler",
    todo_title: "Måste göras idag",
    todo_done: "🎉 Allt klart för idag – bra jobbat!",
    todo_btn: "Klar",
    todo_overdue: "Försenad",
    todo_due: "Ska göras idag",
    todo_failed: "Kunde inte slutföra: {e}",
    bonus_title: "Bonusuppgifter",
    bonus_locked: "🔒 Bonusuppgifter låses upp när dagens uppgifter är klara.",
    bonus_pending: "⏳ {n} bonuspoäng väntar på att läggas till!",
    bonus_none: "Inga bonusuppgifter inställda än.",
    wallet_title: "Plånbok",
    wallet_sub: "Pengar du har sparat",
    t_wallet: "Plånboken",
    adjust_amount: "Belopp (använd - för avdrag)",
    w_recent: "Senaste händelser",
    w_empty: "Inga pengar än. Växla poäng för att fylla plånboken!",
    h_cashout: "Utväxlat",
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
      rewards.map((r) => [r.id, r.st.state, r.st.attributes.cost, r.st.attributes.bank, r.st.attributes.reward, r.st.attributes.payout, r.st.attributes.currency]),
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
      const icon = icons[a.reward] || (a.payout ? "mdi:cash" : kcpIcon(a.reward));
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
                ? `${a.cost} ${this._t("points")}${a.payout ? ` → ${a.payout} ${a.currency}` : ""}`
                : `${a.cost} ${this._t("points")}${a.payout ? ` → ${a.payout} ${a.currency}` : ""} · ${this._t("short", { n: a.cost - a.bank })}`
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
      const costs = rewards.map((r) => kcpEsc(`${r.st.attributes.reward} = ${r.st.attributes.cost} p${r.st.attributes.payout ? ` → ${r.st.attributes.payout} ${r.st.attributes.currency}` : ""}`)).join("<br>");
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
    const tile = (icon, color, primary, secondary, cls = "tile") => `
      <div class="${cls}" style="--c:${color}">
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
            S.wallet?.attributes.enabled
              ? tile("mdi:wallet", "#64d2ff", `${n("wallet")} ${S.wallet.attributes.currency}`, kcpT(h, "wallet_title"), "wide")
              : ""
          }
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
        .stats { display: flex; flex-wrap: wrap; gap: 4px 16px; margin-top: 4px; color: var(--secondary-text-color); }
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
        <div class="stats"><span class="sw"></span><span class="sb"></span><span class="sm"></span></div>
        <label class="l-target"></label>
        <div class="seg"><button data-t="bank"></button><button data-t="week"></button><button data-t="wallet"></button></div>
        <label class="l-points"></label>
        <input class="num" type="text" inputmode="text" autocomplete="off" placeholder="5 / -5" />
        <label class="l-reason"></label>
        <input class="reason" type="text" autocomplete="off" />
        <button class="apply"></button>
        <div class="msg"></div>
      </ha-card>`;
    const $ = (q) => this.shadowRoot.querySelector(q);
    this._el = {
      title: $(".t"), sw: $(".sw"), sb: $(".sb"), sm: $(".sm"),
      lTarget: $(".l-target"), lPoints: $(".l-points"), lReason: $(".l-reason"),
      num: $(".num"), reason: $(".reason"), apply: $(".apply"), msg: $(".msg"),
      bankBtn: $('[data-t="bank"]'), weekBtn: $('[data-t="week"]'), walletBtn: $('[data-t="wallet"]'),
    };
    for (const b of [this._el.bankBtn, this._el.weekBtn, this._el.walletBtn]) {
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
    e.lPoints.textContent = kcpT(h, this._target === "wallet" ? "adjust_amount" : "adjust_points");
    e.lReason.textContent = kcpT(h, "adjust_reason");
    e.apply.textContent = kcpT(h, "apply");
    e.bankBtn.textContent = kcpT(h, "t_bank");
    e.weekBtn.textContent = kcpT(h, "t_week");
    e.walletBtn.textContent = kcpT(h, "t_wallet");
    e.walletBtn.classList.toggle("on", this._target === "wallet");
    e.bankBtn.classList.toggle("on", this._target === "bank");
    e.weekBtn.classList.toggle("on", this._target === "week");
    e.apply.disabled = !S;
    if (!S) {
      e.msg.textContent = kcpT(h, "no_tracker");
      e.msg.classList.add("err");
      e.sw.textContent = e.sb.textContent = e.sm.textContent = "";
      return;
    }
    e.sw.innerHTML = `${kcpEsc(kcpT(h, "this_week"))}: <b>${parseInt(S.points_week?.state, 10) || 0} p</b>`;
    e.sb.innerHTML = `${kcpEsc(kcpT(h, "bank"))}: <b>${parseInt(S.points_bank?.state, 10) || 0} p</b>`;
    e.sm.innerHTML = S.wallet
      ? `${kcpEsc(kcpT(h, "wallet_title"))}: <b>${parseInt(S.wallet.state, 10) || 0} ${kcpEsc(S.wallet.attributes.currency)}</b>`
      : "";
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
    const wallet = this._target === "wallet";
    const data = {
      [wallet ? "amount" : "points"]: points,
      config_entry: (S.points_bank || S.points_week).attributes.entry_id,
    };
    if (!wallet) data.target = this._target;
    const reason = e.reason.value.trim();
    if (reason) data.reason = reason;
    e.apply.disabled = true;
    try {
      await h.callService("kid_chores_points", wallet ? "adjust_wallet" : "adjust_points", data);
      const t = kcpT(h, { bank: "t_bank", week: "t_week", wallet: "t_wallet" }[this._target]);
      const n = wallet ? `${Math.abs(points)} ${S.wallet?.attributes.currency || ""}`.trim() : Math.abs(points);
      this._say(kcpT(h, points > 0 ? "added" : "deducted", { n, t }));
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
  description: "Parent tool: add or deduct points in the bank or this week, or money in the wallet.",
  preview: true,
});


/* ------------------------------------------------------------------ */
/*  History card (parents)                                             */
/* ------------------------------------------------------------------ */
const KCP_HISTORY = {
  chore: ["mdi:check-circle", "#30d158"],
  bonus: ["mdi:star-circle", "#ffd60a"],
  bonus_released: ["mdi:lock-open-check", "#ffd60a"],
  pending: ["mdi:timer-sand", "#8e8e93"],
  redeem: ["mdi:gift", "#ff453a"],
  adjust: ["mdi:tune-vertical", "#0a84ff"],
  wallet: ["mdi:wallet", "#64d2ff"],
  week_close: ["mdi:flag-checkered", "#bf5af2"],
};

class KidChoresHistoryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._shown = 0;
    this._sig = "";
  }

  static getConfigElement() {
    return document.createElement("kid-chores-history-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = config;
    this._shown = 0;
    this._sig = "";
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 6;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  _day(h, d) {
    const today = new Date();
    const y = new Date();
    y.setDate(today.getDate() - 1);
    if (d.toDateString() === today.toDateString()) return kcpT(h, "h_today");
    if (d.toDateString() === y.toDateString()) return kcpT(h, "h_yesterday");
    return d.toLocaleDateString(h.language, { weekday: "long", day: "numeric", month: "short" });
  }

  _render() {
    const h = this._hass, cfg = this._config;
    if (!h || !cfg) return;
    const S = kcpSensors(h, cfg.device);
    const st = S?.points_history;
    const sig = [h.language, st?.last_updated, st?.state].join("|");
    if (sig === this._sig) return;
    this._sig = sig;

    const step = Math.max(parseInt(cfg.limit, 10) || 30, 1);
    if (!this._shown) this._shown = step;
    const all = st?.attributes.history || [];
    const rows = all.slice(0, this._shown);
    const balances = cfg.show_balances !== false;

    let body = "";
    if (!S) body = `<div class="empty">${kcpEsc(kcpT(h, "no_tracker"))}</div>`;
    else if (!rows.length) body = `<div class="empty">${kcpEsc(kcpT(h, "h_empty"))}</div>`;
    let day = "";
    for (const r of rows) {
      const d = new Date(r.t);
      const dl = this._day(h, d);
      if (dl !== day) {
        day = dl;
        body += `<div class="day">${kcpEsc(dl)}</div>`;
      }
      const [icon, color] =
        r.type === "adjust" && r.target === "wallet" ? KCP_HISTORY.wallet : KCP_HISTORY[r.type] || KCP_HISTORY.adjust;
      const isWallet = r.target === "wallet";
      const cur = S?.wallet?.attributes.currency || "";
      const pts = r.type === "pending" ? r.pending : isWallet ? r.amount : r.points;
      const unit = isWallet ? cur : "p";
      const sign = pts > 0 ? "+" : "";
      const cls = r.type === "pending" ? "pend" : pts < 0 ? "neg" : pts > 0 ? "pos" : "";
      const where = r.target === "bank" && r.type !== "redeem" ? ` ${kcpT(h, "h_to_bank")}` : "";
      // cashing out points also adds money to the wallet
      const gain = r.type === "redeem" && r.amount ? `+${r.amount} ${cur}` : "";
      const label = r.label || (r.type === "adjust" ? kcpT(h, "h_no_reason") : "");
      const time = d.toLocaleTimeString(h.language, { hour: "2-digit", minute: "2-digit" });
      const sub = [
        kcpT(h, r.type === "redeem" && r.amount ? "h_cashout" : `h_${r.type}`) +
          (r.type === "adjust" ? ` (${kcpT(h, { bank: "t_bank", week: "t_week", wallet: "t_wallet" }[r.target] || "t_week")})` : ""),
        time,
      ].join(" · ");
      body += `
        <div class="row">
          <div class="dot" style="--c:${color}"><ha-icon icon="${icon}"></ha-icon></div>
          <div class="main">
            <div class="lbl">${kcpEsc(label)}</div>
            <div class="sub">${kcpEsc(sub)}</div>
            ${balances ? `<div class="sub">${kcpEsc(kcpT(h, "h_balances", { w: r.week, b: r.bank }) + (r.wallet !== undefined && S?.wallet?.attributes.enabled ? ` · ${kcpT(h, "wallet_title")} ${r.wallet} ${cur}` : ""))}</div>` : ""}
          </div>
          <div class="pts ${cls}">${sign}${pts} ${kcpEsc(unit)}${kcpEsc(where)}${gain ? `<div class="gain">${kcpEsc(gain)}</div>` : ""}</div>
        </div>`;
    }
    const more = all.length > rows.length
      ? `<button class="more">${kcpEsc(kcpT(h, "h_more"))}</button>` : "";

    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .t { font-size: 1.4em; font-weight: 600; color: var(--primary-text-color); margin-bottom: 4px; }
        .day { margin: 16px 0 6px; font-size: .85em; font-weight: 600; text-transform: capitalize;
          color: var(--secondary-text-color); }
        .row { display: flex; align-items: center; gap: 12px; padding: 8px 0; position: relative; }
        .row:not(:last-child) .dot::after { content: ""; position: absolute; left: 17px; top: 44px;
          bottom: -8px; width: 2px; background: var(--divider-color, #888); opacity: .5; }
        .dot { position: relative; flex: none; width: 36px; height: 36px; border-radius: 50%;
          display: flex; align-items: center; justify-content: center; color: var(--c);
          background: color-mix(in srgb, var(--c) 18%, transparent); }
        .main { flex: 1; min-width: 0; }
        .lbl { color: var(--primary-text-color); overflow-wrap: anywhere; }
        .sub { font-size: .8em; color: var(--secondary-text-color); }
        .pts { flex: none; font-weight: 600; text-align: right; color: var(--primary-text-color); }
        .pts.pos { color: var(--success-color, #30d158); }
        .pts.neg { color: var(--error-color, #ff453a); }
        .pts.pend { color: var(--secondary-text-color); }
        .pts .gain { color: var(--success-color, #30d158); }
        .empty { padding: 16px 0; color: var(--secondary-text-color); }
        .more { width: 100%; margin-top: 12px; padding: 10px; border: 1px solid var(--divider-color, #888);
          border-radius: 10px; background: transparent; font: inherit; cursor: pointer;
          color: var(--primary-text-color); }
      </style>
      <ha-card>
        <div class="t">${kcpEsc(cfg.title ?? kcpT(h, "history_title"))}</div>
        ${body}${more}
      </ha-card>`;
    this.shadowRoot.querySelector(".more")?.addEventListener("click", () => {
      this._shown += step;
      this._sig = "";
      this._render();
    });
  }
}

class KidChoresHistoryCardEditor extends KidChoresStatusCardEditor {}

customElements.define("kid-chores-history-card", KidChoresHistoryCard);
customElements.define("kid-chores-history-card-editor", KidChoresHistoryCardEditor);
window.customCards.push({
  type: "kid-chores-history-card",
  name: "Kid Chores & Points – History",
  description: "Parent view: timeline of every points change and the reason for it.",
  preview: true,
});


/* ------------------------------------------------------------------ */
/*  Chores to do today (mandatory chores + Maintenance Supporter)      */
/* ------------------------------------------------------------------ */
const KCP_ACTIONABLE = ["overdue", "triggered", "due_soon"];

class KidChoresTodoCard extends HTMLElement {
  static LABEL = "mandatory";
  static TITLE = "todo_title";

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._sig = "";
    this._tasks = []; // actionable Maintenance Supporter tasks
    this._busy = new Set();
    this._notes = new Map(); // task name -> Maintenance Supporter notes
    this._open = new Set(); // names with expanded notes
    this._error = "";
    this._msSig = null;
  }

  static getConfigElement() {
    return document.createElement("kid-chores-todo-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = config;
    this._sig = "";
    this._msSig = null;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._syncTasks();
    this._render();
  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  /* Re-fetch the Maintenance Supporter tasks whenever one of its sensors changes. */
  _syncTasks() {
    const h = this._hass;
    if (!h?.entities || !this._config) return;
    let sig = "";
    for (const [id, reg] of Object.entries(h.entities)) {
      if (reg.platform !== "maintenance_supporter") continue;
      const st = h.states[id];
      if (st) sig += `${id}:${st.state}:${st.last_updated};`;
    }
    if (sig === this._msSig) return;
    this._msSig = sig;
    this._fetchTasks();
  }

  async _fetchTasks() {
    const labels = this._config.filter_labels ?? [this.constructor.LABEL];
    const statuses = this._config.filter_status ?? KCP_ACTIONABLE;
    try {
      const res = await this._hass.connection.sendMessagePromise({
        type: "maintenance_supporter/objects",
        compact: true,
      });
      const tasks = [];
      const notes = new Map();
      for (const obj of res.objects || []) {
        if (obj.object?.archived) continue;
        for (const t of obj.tasks || []) {
          if (t.archived || t.is_done || !t.sensor_entity_id) continue;
          if (t.notes && String(t.notes).trim()) notes.set(t.name, String(t.notes).trim());
          const labelOk = !labels.length || (t.labels || []).some((l) => labels.includes(l));
          tasks.push({ name: t.name, entity: t.sensor_entity_id, status: t.status, actionable: labelOk && statuses.includes(t.status) });
        }
      }
      this._tasks = tasks;
      this._notes = notes;
    } catch {
      this._tasks = [];
      this._notes = new Map(); // Maintenance Supporter not installed / not reachable
    }
    this._sig = "";
    this._render();
  }

  _lead() {
    return "";
  }

  _tail(rows) {
    const h = this._hass;
    return rows.some((r) => !r.done) ? "" : `<div class="all">${kcpEsc(kcpT(h, "todo_done"))}</div>`;
  }

  _rows() {
    const S = kcpSensors(this._hass, this._config.device);
    const attrs = S?.mandatory_remaining?.attributes;
    if (!attrs) return null;
    const pts = attrs.mandatory_chores || {};
    const byName = new Map(this._tasks.map((t) => [t.name, t]));
    const rows = [];
    for (const name of attrs.done || []) rows.push({ name, done: true, pts: pts[name] });
    for (const name of attrs.remaining || []) {
      const t = byName.get(name);
      byName.delete(name);
      // A chore that exists in Maintenance Supporter is only shown while it matches the filters.
      if (t && !t.actionable) continue;
      rows.push({ name, done: false, pts: pts[name], ms: t || null });
    }
    for (const t of byName.values()) {
      if (t.actionable) rows.push({ name: t.name, done: false, ms: t });
    }
    return rows.filter((r, i, all) => all.findIndex((x) => x.name === r.name) === i);
  }

  _render() {
    const h = this._hass, cfg = this._config;
    if (!h || !cfg) return;
    const rows = this._rows();
    if (rows) for (const r of rows) r.notes = this._notes.get(r.name) || "";
    const sig = JSON.stringify([rows, h.language, cfg, [...this._busy], [...this._open], this._error, rows && this._lead(rows)]);
    if (sig === this._sig) return;
    this._sig = sig;

    let body;
    if (!rows) {
      body = `<div class="empty">${kcpEsc(kcpT(h, "no_tracker"))}</div>`;
    } else {
      body = this._lead(rows) + rows
        .map((r, i) => {
          const c = r.done ? "#30d158" : "#ffd60a";
          const sub = [r.pts !== undefined ? `+${r.pts} p` : "",
            r.ms?.status === "overdue" ? kcpT(h, "todo_overdue") : ""].filter(Boolean).join(" · ");
          const busy = r.ms && this._busy.has(r.ms.entity);
          return `
            <div class="row ${r.done ? "done" : ""} ${r.notes ? "has-notes" : ""}" data-i="${i}" style="--c:${c}">
              <div class="ico"><ha-icon icon="${r.done ? "mdi:checkbox-marked-circle" : r.icon || "mdi:checkbox-blank-circle-outline"}"></ha-icon></div>
              <div class="txt">
                <div class="primary">${kcpEsc(r.name)}</div>
                ${sub ? `<div class="secondary">${kcpEsc(sub)}</div>` : ""}
              </div>
              ${r.notes ? `<ha-icon class="info" icon="${this._open.has(r.name) ? "mdi:chevron-up" : "mdi:information-outline"}"></ha-icon>` : ""}
              ${r.ms ? `<button class="btn" data-i="${i}" ${busy ? "disabled" : ""}><ha-icon icon="mdi:check"></ha-icon>${kcpEsc(kcpT(h, "todo_btn"))}</button>` : ""}
              ${r.notes && this._open.has(r.name) ? `<div class="notes">${kcpEsc(r.notes).replace(/\n/g, "<br>")}</div>` : ""}
            </div>`;
        })
        .join("");
      body += this._tail(rows);
    }

    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .t { font-size: 1.4em; font-weight: 600; color: var(--primary-text-color); margin-bottom: 12px; }
        .row { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; padding: 10px 12px; margin-top: 8px;
          background: var(--secondary-background-color, rgba(127,127,127,.1));
          border-left: 4px solid var(--c); border-radius: 12px; }
        .ico { width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; flex: none;
          color: var(--c); background: color-mix(in srgb, var(--c) 20%, transparent); }
        .txt { flex: 1; min-width: 0; }
        .primary { font-weight: 600; color: var(--primary-text-color); overflow-wrap: anywhere; }
        .secondary { font-size: .9em; color: var(--secondary-text-color); }
        .row.done .primary { text-decoration: line-through; color: var(--secondary-text-color); font-weight: 400; }
        .btn { flex: none; display: inline-flex; align-items: center; gap: 6px; padding: 10px 16px; border: 0;
          border-radius: 10px; font: inherit; font-weight: 600; cursor: pointer; --mdc-icon-size: 18px;
          background: var(--primary-color); color: var(--text-primary-color, #fff); }
        .btn:disabled { opacity: .5; cursor: default; }
        .all { margin-top: 12px; padding: 12px; text-align: center; font-weight: 600;
          color: var(--primary-text-color); }
        .empty { color: var(--secondary-text-color); }
        .row.has-notes { cursor: pointer; }
        .info { flex: none; color: var(--secondary-text-color); --mdc-icon-size: 20px; }
        .notes { flex: 1 0 100%; padding-top: 8px; border-top: 1px solid var(--divider-color, rgba(127,127,127,.3));
          font-size: .95em; color: var(--primary-text-color); overflow-wrap: anywhere; cursor: default; }
        .lock { padding: 4px 0; color: var(--primary-text-color); }
        .err { margin-top: 10px; font-size: .9em; color: var(--error-color, #db4437); }
      </style>
      <ha-card>
        <div class="t">${kcpEsc(cfg.title ?? kcpT(h, this.constructor.TITLE))}</div>
        ${body}
        ${this._error ? `<div class="err">${kcpEsc(this._error)}</div>` : ""}
      </ha-card>`;

    this.shadowRoot.querySelectorAll(".btn").forEach((el) => {
      el.addEventListener("click", (ev) => {
        ev.stopPropagation();
        this._complete(rows[Number(el.dataset.i)].ms);
      });
    });
    this.shadowRoot.querySelectorAll(".row.has-notes").forEach((el) => {
      el.addEventListener("click", (ev) => {
        if (ev.target.closest(".notes")) return;
        const name = rows[Number(el.dataset.i)].name;
        if (!this._open.delete(name)) this._open.add(name);
        this._sig = "";
        this._render();
      });
    });
  }

  async _complete(task) {
    if (!task || this._busy.has(task.entity)) return;
    this._busy.add(task.entity);
    this._error = "";
    this._render();
    try {
      await this._hass.callService("maintenance_supporter", "complete", { entity_id: task.entity });
    } catch (err) {
      this._error = kcpT(this._hass, "todo_failed", { e: err?.message || err });
    }
    this._busy.delete(task.entity);
    this._sig = "";
    this._render();
  }
}

class KidChoresTodoCardEditor extends HTMLElement {
  static LABEL = "mandatory";

  constructor() {
    super();
    this._labels = [];
    this._labelsLoaded = false;
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._labelsLoaded) this._loadLabels();
    if (this._form) this._form.hass = hass;
    else this._render();
  }

  async _loadLabels() {
    this._labelsLoaded = true;
    try {
      const res = await this._hass.connection.sendMessagePromise({
        type: "maintenance_supporter/objects",
        compact: true,
      });
      const found = new Set();
      for (const o of res.objects || []) for (const t of o.tasks || []) for (const l of t.labels || []) found.add(l);
      this._labels = [...found].sort();
    } catch {
      this._labels = [];
    }
    this._schema = null;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;
    const cfgLabels = this._config.filter_labels ?? [this.constructor.LABEL];
    const labels = [...new Set([...this._labels, ...cfgLabels])];
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) =>
        ({
          device: "Tracker (leave empty for the first one)",
          title: "Title",
          filter_labels: "Maintenance Supporter labels to show (none = all tasks)",
          filter_status: "Show a task as open when its status is",
        }[s.name] || s.name);
      this._form.addEventListener("value-changed", (ev) => {
        const config = { type: this._config.type, ...ev.detail.value };
        for (const k of ["device", "title"]) if (config[k] === "" || config[k] === undefined) delete config[k];
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    const statuses = ["overdue", "triggered", "due_soon", "ok"];
    const key = labels.join("|");
    if (this._schemaKey !== key) {
      this._schemaKey = key;
      this._form.schema = [
        { name: "device", selector: { device: { integration: "kid_chores_points" } } },
        { name: "title", selector: { text: {} } },
        {
          name: "filter_labels",
          selector: { select: { multiple: true, custom_value: true, mode: "dropdown", options: labels } },
        },
        {
          name: "filter_status",
          selector: { select: { multiple: true, mode: "list", options: statuses } },
        },
      ];
    }
    this._form.hass = this._hass;
    this._form.data = {
      filter_labels: [this.constructor.LABEL],
      filter_status: KCP_ACTIONABLE,
      ...this._config,
    };
  }
}

customElements.define("kid-chores-todo-card", KidChoresTodoCard);
customElements.define("kid-chores-todo-card-editor", KidChoresTodoCardEditor);
window.customCards.push({
  type: "kid-chores-todo-card",
  name: "Kid Chores & Points – Chores to do",
  description: "Today's mandatory chores, one per line with ticks, plus Done buttons for the matching Maintenance Supporter tasks.",
  preview: true,
});


/* ------------------------------------------------------------------ */
/*  Bonus chores (unlock when the mandatory chores are done)           */
/* ------------------------------------------------------------------ */
class KidChoresBonusCard extends KidChoresTodoCard {
  static LABEL = "bonus";
  static TITLE = "bonus_title";

  static getConfigElement() {
    return document.createElement("kid-chores-bonus-card-editor");
  }

  _locked() {
    const S = kcpSensors(this._hass, this._config.device);
    return (S?.mandatory_remaining?.attributes.remaining || []).length > 0;
  }

  _lead() {
    const h = this._hass;
    const S = kcpSensors(h, this._config.device);
    const pending = parseInt(S?.pending_bonus?.state, 10) || 0;
    let out = "";
    if (this._locked()) out += `<div class="lock">${kcpEsc(kcpT(h, "bonus_locked"))}</div>`;
    if (pending > 0) out += `<div class="lock">${kcpEsc(kcpT(h, "bonus_pending", { n: pending }))}</div>`;
    return out;
  }

  _tail(rows) {
    if (this._locked() || rows.length) return "";
    return `<div class="empty">${kcpEsc(kcpT(this._hass, "bonus_none"))}</div>`;
  }

  _rows() {
    const S = kcpSensors(this._hass, this._config.device);
    const attrs = S?.mandatory_remaining?.attributes;
    if (!attrs) return null;
    if (this._locked()) return [];
    const doneToday = S.points_today?.attributes.bonus_done || [];
    const byName = new Map(this._tasks.map((t) => [t.name, t]));
    const rows = [];
    for (const [name, pts] of Object.entries(attrs.bonus_chores || {})) {
      const t = byName.get(name);
      byName.delete(name);
      const ms = t?.actionable ? t : null;
      const done = !ms && doneToday.includes(name);
      // A chore that exists in Maintenance Supporter is only shown while it matches the filters
      // (or as ticked, if it was already done today).
      if (t && !ms && !done) continue;
      rows.push({ name, pts, ms, done, icon: "mdi:star-circle-outline" });
    }
    for (const t of byName.values()) {
      if (t.actionable) rows.push({ name: t.name, ms: t, done: false, icon: "mdi:star-circle-outline" });
    }
    return rows;
  }
}

class KidChoresBonusCardEditor extends KidChoresTodoCardEditor {
  static LABEL = "bonus";
}

customElements.define("kid-chores-bonus-card", KidChoresBonusCard);
customElements.define("kid-chores-bonus-card-editor", KidChoresBonusCardEditor);
window.customCards.push({
  type: "kid-chores-bonus-card",
  name: "Kid Chores & Points – Bonus chores",
  description: "Bonus chores with Done buttons for Maintenance Supporter tasks; locked until today's mandatory chores are done.",
  preview: true,
});


/* ------------------------------------------------------------------ */
/*  Wallet card (child)                                                */
/* ------------------------------------------------------------------ */
class KidChoresWalletCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._sig = "";
  }

  static getConfigElement() {
    return document.createElement("kid-chores-wallet-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = config;
    this._sig = "";
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  _render() {
    const h = this._hass, cfg = this._config;
    if (!h || !cfg) return;
    const S = kcpSensors(h, cfg.device);
    const w = S?.wallet;
    const hist = S?.points_history;
    const sig = [h.language, w?.state, w?.attributes.currency, hist?.last_updated, hist?.state, JSON.stringify(cfg)].join("|");
    if (sig === this._sig) return;
    this._sig = sig;

    const cur = w?.attributes.currency || "";
    const limit = Math.max(parseInt(cfg.limit, 10) || 5, 1);
    // wallet movements: manual adjustments and point cash-outs
    const rows = (hist?.attributes.history || [])
      .filter((r) => r.target === "wallet" || (r.type === "redeem" && r.amount))
      .slice(0, limit);

    let body = "";
    if (!S) body = `<div class="empty">${kcpEsc(kcpT(h, "no_tracker"))}</div>`;
    else if (!rows.length) body = `<div class="empty">${kcpEsc(kcpT(h, "w_empty"))}</div>`;
    else {
      body = `<div class="sec">${kcpEsc(kcpT(h, "w_recent"))}</div>`;
      for (const r of rows) {
        const d = new Date(r.t);
        const amount = r.amount;
        const label = r.type === "redeem" ? r.label : r.label || kcpT(h, "h_no_reason");
        const sub = [
          kcpT(h, r.type === "redeem" ? "h_cashout" : "h_adjust"),
          d.toLocaleDateString(h.language, { day: "numeric", month: "short" }),
        ].join(" · ");
        body += `
          <div class="row">
            <div class="main"><div class="lbl">${kcpEsc(label)}</div><div class="sub">${kcpEsc(sub)}</div></div>
            <div class="amt ${amount < 0 ? "neg" : "pos"}">${amount > 0 ? "+" : ""}${amount} ${kcpEsc(cur)}</div>
          </div>`;
      }
    }

    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .t { font-size: 1.4em; font-weight: 600; color: var(--primary-text-color); }
        .s { color: var(--secondary-text-color); margin-top: 2px; }
        .bal { display: flex; align-items: center; gap: 14px; margin-top: 14px; padding: 14px 16px;
          border-left: 4px solid var(--c); border-radius: 12px; --c: #64d2ff;
          background: var(--secondary-background-color, rgba(127,127,127,.1)); }
        .ico { width: 48px; height: 48px; border-radius: 50%; display: grid; place-items: center; flex: none;
          color: var(--c); background: color-mix(in srgb, var(--c) 20%, transparent); --mdc-icon-size: 28px; }
        .big { font-size: 2em; font-weight: 700; color: var(--primary-text-color); line-height: 1.1; }
        .sec { margin: 16px 0 4px; font-size: .85em; font-weight: 600; color: var(--secondary-text-color); }
        .row { display: flex; align-items: center; gap: 12px; padding: 8px 0; }
        .row:not(:last-child) { border-bottom: 1px solid var(--divider-color, rgba(127,127,127,.3)); }
        .main { flex: 1; min-width: 0; }
        .lbl { color: var(--primary-text-color); overflow-wrap: anywhere; }
        .sub { font-size: .8em; color: var(--secondary-text-color); }
        .amt { flex: none; font-weight: 600; }
        .amt.pos { color: var(--success-color, #30d158); }
        .amt.neg { color: var(--error-color, #ff453a); }
        .empty { padding: 16px 0 0; color: var(--secondary-text-color); }
      </style>
      <ha-card>
        <div class="t">${kcpEsc(cfg.title ?? kcpT(h, "wallet_title"))}</div>
        ${
          S
            ? `<div class="bal">
                <div class="ico"><ha-icon icon="mdi:wallet"></ha-icon></div>
                <div><div class="big">${parseInt(w?.state, 10) || 0} ${kcpEsc(cur)}</div>
                <div class="s">${kcpEsc(kcpT(h, "wallet_sub"))}</div></div>
              </div>`
            : ""
        }
        ${body}
      </ha-card>`;
  }
}

class KidChoresWalletCardEditor extends KidChoresStatusCardEditor {}

customElements.define("kid-chores-wallet-card", KidChoresWalletCard);
customElements.define("kid-chores-wallet-card-editor", KidChoresWalletCardEditor);
window.customCards.push({
  type: "kid-chores-wallet-card",
  name: "Kid Chores & Points – Wallet",
  description: "The child's wallet: current money and recent cash-outs and adjustments.",
  preview: true,
});
