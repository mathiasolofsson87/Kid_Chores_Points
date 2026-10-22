import { kcpCount, kcpEsc, kcpPick, kcpT, kcpSensors } from "../helpers.js";

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
      S?.bonus_week?.attributes.enabled,
      S?.wallet?.attributes.enabled,
      S?.wallet?.attributes.currency,
      S?.day_streak?.attributes,
      S?.week_streak?.attributes,
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
        <div class="txt"><div class="primary">${kcpEsc(primary)}</div>${[].concat(secondary).map((l) => `<div class="secondary">${kcpEsc(l)}</div>`).join("")}</div>
      </div>`;

    // One streak tile (only when switched on under Configure -> Streaks & medals): the streak
    // that is closest to its next medal, a day streak or a week streak (a week counts as 7 days).
    let streaks = "";
    const day = S.day_streak;
    if (day?.attributes.enabled) {
      const week = S.week_streak;
      const dayNext = day.attributes.next;
      const weekNext = week?.attributes.next;
      const weekCloser = weekNext && (!dayNext || weekNext.remaining * 7 < dayNext.remaining);
      const [src, unit, next] = weekCloser ? [week, "week", weekNext] : [day, "day", dayNext];
      const count = parseInt(src.state, 10) || 0;
      const lines = [
        next
          ? kcpT(h, "streak_next", { n: next.remaining, name: kcpPick(h, next, "name") })
          : kcpT(h, "streak_best", { n: src.attributes.best }),
      ];
      const risk = day.attributes.at_risk;
      if (risk) lines.push(kcpT(h, "streak_risk", { n: parseInt(day.state, 10) || 0 }));
      streaks = tile("mdi:trophy-outline", risk ? "#ff9f0a" : "#bf5af2", kcpCount(h, unit, count), lines, "wide");
    }

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
        .bonus { display: flex; align-items: center; gap: 10px; margin-top: 12px; padding: 8px 12px;
          border-radius: 12px; background: color-mix(in srgb, var(--c) 14%, transparent);
          border: 1px solid color-mix(in srgb, var(--c) 40%, transparent); }
        .bonus .star { font-size: 1.5em; line-height: 1; flex: none; }
        .bonus .primary { font-size: .95em; }
        .bonus .secondary { font-size: .8em; }
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
          ${
            S.bonus_week?.attributes.enabled
              ? (([head, note]) => `<div class="bonus" style="--c:${pct >= 100 ? "#30d158" : "#ffd60a"}">
                  <span class="star">⭐</span>
                  <div class="txt"><div class="primary">${kcpEsc(head.replace(/^⭐\s*/, ""))}</div><div class="secondary">${kcpEsc(note || "")}</div></div>
                </div>`)(kcpT(h, pct >= 100 ? "bonus_met" : "bonus_open", { n: n("bonus_week") }).split("\n"))
              : ""
          }
        </div>
        <div class="grid">
          ${tile("mdi:star", "#ffd60a", `${n("points_week")} p`, kcpT(h, "this_week"))}
          ${tile("mdi:flag-variant", "#0a84ff", `${n("points_to_goal")} p`, kcpT(h, "to_goal"))}
          ${tile("mdi:calendar-check", "#30d158", `${n("points_today")} p`, kcpT(h, "today"))}
          ${tile("mdi:piggy-bank", "#ff9f0a", `${n("points_bank")} p`, kcpT(h, "bank"))}
          ${streaks}
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

export { KidChoresStatusCardEditor };
