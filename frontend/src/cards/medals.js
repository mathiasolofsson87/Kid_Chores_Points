import { kcpCount, kcpEsc, kcpPick, kcpT, kcpSensors } from "../helpers.js";
import { kcpMedalSvg } from "../medal-icons.js";
import { KidChoresStatusCardEditor } from "./status.js";

/* ------------------------------------------------------------------ */
/*  Medals card (child)                                                */
/* ------------------------------------------------------------------ */
// medal kinds shown together, in this order
const KCP_MEDAL_SECTIONS = [
  ["m_streaks", ["day", "week"], "#f2603a"],
  ["m_chores", ["chores", "treat"], "#3b82f6"],
  ["m_bonus", ["bonus"], "#8b5cf6"],
];
const KCP_NEW_DAYS = 2; // a medal is "new" this many days after it was earned

class KidChoresMedalsCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._sig = "";
  }

  static getConfigElement() {
    return document.createElement("kid-chores-medals-card-editor");
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
    return 6;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  _isNew(date) {
    const age = (Date.now() - new Date(`${date}T00:00:00`).getTime()) / 86400000;
    return age < KCP_NEW_DAYS + 1;
  }

  _tile(h, m) {
    const earned = !!m.earned;
    let sub;
    if (earned) {
      const d = new Date(`${m.earned}T00:00:00`).toLocaleDateString(h.language, { day: "numeric", month: "short" });
      sub = `<div class="sub">${kcpEsc(kcpT(h, "m_earned", { d }))}</div>`;
    } else {
      const unit = { day: "pu_day", week: "pu_week", chores: "pu_chores", bonus: "pu_bonus" }[m.kind];
      const text = unit ? `${m.progress} / ${m.at} ${kcpT(h, unit)}` : kcpT(h, "m_not_yet");
      const pct = Math.min(100, Math.round((m.progress / m.at) * 100));
      sub = `<div class="how">${kcpEsc(kcpPick(h, m, "how"))}</div>
        <div class="bar"><div style="width:${pct}%"></div></div>
        <div class="sub">${kcpEsc(text)}</div>`;
    }
    const bonus = m.bonus ? `<span class="pill">+${m.bonus} p</span>` : "";
    const flag = earned && this._isNew(m.earned) ? `<span class="new">${kcpEsc(kcpT(h, "m_new"))}</span>` : "";
    return `<div class="medal ${earned ? "got" : "lock"}" data-id="${kcpEsc(m.id)}">
      ${flag}
      <div class="art">${kcpMedalSvg(m.id, 72)}</div>
      <div class="name">${kcpEsc(kcpPick(h, m, "name"))}</div>
      ${sub}
      ${earned ? "" : bonus}
    </div>`;
  }

  _render() {
    const h = this._hass, cfg = this._config;
    if (!h || !cfg) return;
    const S = kcpSensors(h, cfg.device);
    const med = S?.medals;
    const sig = [
      h.language,
      med?.state,
      JSON.stringify(med?.attributes),
      S?.day_streak?.state,
      S?.week_streak?.state,
      S?.day_streak?.attributes.best,
      S?.week_streak?.attributes.best,
      new Date().toDateString(),
      JSON.stringify(cfg),
    ].join("|");
    if (sig === this._sig) return;
    this._sig = sig;

    const title = cfg.title ?? kcpT(h, "medals_title");
    let body = "";
    let summary = "";
    if (!S) body = `<div class="empty">${kcpEsc(kcpT(h, "no_tracker"))}</div>`;
    else if (!med?.attributes.enabled) body = `<div class="empty">${kcpEsc(kcpT(h, "medals_off"))}</div>`;
    else {
      const shown = med.attributes.medals.filter((m) => m.available);
      const got = shown.filter((m) => m.earned).length;
      const streak = (key, unit, icon) => {
        const n = parseInt(S[key]?.state, 10) || 0;
        return `<span class="chip"><ha-icon icon="${icon}"></ha-icon>${kcpEsc(kcpCount(h, unit, n))}</span>`;
      };
      // the best streak ever: once it passed 14 days it is shown in weeks, and it only changes
      // when it is beaten, not when the current streak resets
      const bestDay = parseInt(S.day_streak?.attributes.best, 10) || 0;
      const bestWeek = parseInt(S.week_streak?.attributes.best, 10) || 0;
      const inWeeks = bestDay > 14 && bestWeek > 0;
      const [bestUnit, bestN] = inWeeks ? ["week", bestWeek] : ["day", bestDay];
      const best = bestN
        ? `<span class="chip"><ha-icon icon="mdi:podium-gold"></ha-icon>${kcpEsc(kcpT(h, "streak_best", { n: kcpCount(h, bestUnit, bestN) }))}</span>`
        : "";
      summary = `<div class="chips">
        ${streak("day_streak", "day", "mdi:fire")}${streak("week_streak", "week", "mdi:trophy-outline")}${best}
        <span class="chip"><ha-icon icon="mdi:medal"></ha-icon>${kcpEsc(kcpT(h, "medals_count", { n: got, total: shown.length }))}</span>
      </div>`;
      for (const [key, kinds, color] of KCP_MEDAL_SECTIONS) {
        const list = shown.filter((m) => kinds.includes(m.kind));
        if (!list.length) continue;
        body += `<div class="sec"><span class="dot" style="background:${color}"></span>${kcpEsc(kcpT(h, key))}
          <span class="cnt">${list.filter((m) => m.earned).length}/${list.length}</span></div>
          <div class="grid">${list.map((m) => this._tile(h, m)).join("")}</div>`;
      }
    }

    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .t { font-size: 1.4em; font-weight: 600; color: var(--primary-text-color); }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 16px;
          background: var(--secondary-background-color, rgba(127,127,127,.1)); color: var(--primary-text-color);
          font-size: .9em; --mdc-icon-size: 18px; }
        .sec { display: flex; align-items: center; gap: 8px; margin: 18px 0 8px; font-weight: 600; color: var(--primary-text-color); }
        .dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
        .cnt { margin-left: auto; font-weight: 400; font-size: .85em; color: var(--secondary-text-color); }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
        .medal { position: relative; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 2px;
          padding: 12px 8px 10px; border-radius: 12px; min-width: 0;
          background: var(--secondary-background-color, rgba(127,127,127,.1)); }
        .art { line-height: 0; }
        .lock .art svg { filter: grayscale(1) opacity(.42); }
        .name { margin-top: 4px; font-weight: 600; color: var(--primary-text-color); overflow-wrap: anywhere; }
        .lock .name { color: var(--secondary-text-color); }
        .sub { font-size: .8em; color: var(--secondary-text-color); font-variant-numeric: tabular-nums; }
        .how { font-size: .8em; color: var(--secondary-text-color); }
        .bar { width: 100%; height: 6px; border-radius: 3px; margin-top: 6px; overflow: hidden;
          background: var(--divider-color, rgba(127,127,127,.3)); }
        .bar div { height: 100%; border-radius: 3px; background: var(--primary-color); }
        .pill { margin-top: 6px; padding: 1px 9px; border-radius: 10px; font-size: .75em; font-weight: 700;
          background: color-mix(in srgb, #ffd60a 28%, transparent); color: var(--primary-text-color); }
        .new { position: absolute; top: 8px; right: 8px; padding: 1px 7px; border-radius: 9px;
          background: #ff453a; color: #fff; font-size: .7em; font-weight: 700; letter-spacing: .04em; }
        .empty { padding: 16px 0 0; color: var(--secondary-text-color); }
      </style>
      <ha-card>
        <div class="t">${kcpEsc(title)}</div>
        ${summary}
        ${body}
      </ha-card>`;
  }
}

class KidChoresMedalsCardEditor extends KidChoresStatusCardEditor {}

customElements.define("kid-chores-medals-card", KidChoresMedalsCard);
customElements.define("kid-chores-medals-card-editor", KidChoresMedalsCardEditor);
window.customCards.push({
  type: "kid-chores-medals-card",
  name: "Kid Chores & Points – Medals",
  description: "Streaks and medals: what the child has earned and how far they are from the next ones.",
  preview: true,
});
