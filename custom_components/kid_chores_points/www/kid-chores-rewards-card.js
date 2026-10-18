/* Kid Chores & Points – rewards card.
 * Served by the integration and auto-loaded on every dashboard.
 * Add via: Edit dashboard -> Add card -> "Kid Chores & Points – Rewards".
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
    this._config = { show_unaffordable: false, color: "#30d158", ...config };
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

    if (rewards.length && !anyAffordable) {
      const costs = rewards.map((r) => `${r.st.attributes.reward} = ${r.st.attributes.cost} p`).join(" · ");
      body += `
        <div class="row hint" style="--c:var(--disabled-text-color, #9e9e9e)">
          <div class="ico"><ha-icon icon="mdi:arm-flex"></ha-icon></div>
          <div class="txt"><div class="primary">${this._t("collect")}</div><div class="secondary">${kcpEsc(costs)}</div></div>
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
        ({ device: "Tracker (leave empty for the first one)", title: "Title", show_unaffordable: "Also show rewards that can't be afforded yet", color: "Accent colour" }[s.name] || s.name);
      this._form.schema = [
        { name: "device", selector: { device: { integration: "kid_chores_points" } } },
        { name: "title", selector: { text: {} } },
        { name: "show_unaffordable", selector: { boolean: {} } },
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
    this._form.data = { show_unaffordable: false, ...this._config };
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
