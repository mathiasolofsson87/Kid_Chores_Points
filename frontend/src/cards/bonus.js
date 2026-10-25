import { kcpEsc, kcpT, kcpSensors } from "../helpers.js";
import { KidChoresTodoCard, KidChoresTodoCardEditor } from "./todo.js";

/* ------------------------------------------------------------------ */
/*  Bonus chores (points are held until the mandatory chores are done) */
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

  _lead(rows) {
    const h = this._hass;
    const S = kcpSensors(h, this._config.device);
    const pending = parseInt(S?.pending_bonus?.state, 10) || 0;
    const locked = this._locked();
    // bonus points already added to the bank today (only once the mandatory chores are done)
    const bonus = S?.mandatory_remaining?.attributes.bonus_chores || {};
    const earned = locked
      ? 0
      : (S?.points_today?.attributes.bonus_done || []).reduce((sum, n) => sum + (Number(bonus[n]) || 0), 0);
    let text, color = "#ffd60a";
    if (locked && pending > 0) text = kcpT(h, "bonus_waiting", { n: pending });
    else if (earned > 0) [text, color] = [kcpT(h, "bonus_earned", { n: earned }), "#30d158"];
    else if (rows?.length) text = kcpT(h, locked ? "bonus_locked" : "bonus_go");
    else return "";
    const [head, note] = text.split("\n");
    return `<div class="bonus" style="--c:${color}">
      <span class="star">⭐</span>
      <div class="txt"><div class="primary">${kcpEsc(head.replace(/^⭐\s*/, ""))}</div><div class="secondary">${kcpEsc(note || "")}</div></div>
    </div>`;
  }

  _tail(rows) {
    if (rows.length) return "";
    return `<div class="empty">${kcpEsc(kcpT(this._hass, "bonus_none"))}</div>`;
  }

  _rows() {
    const S = kcpSensors(this._hass, this._config.device);
    const attrs = S?.mandatory_remaining?.attributes;
    if (!attrs) return null;
    // done today, or done and waiting for the mandatory chores (its points are held)
    const doneToday = [
      ...(S.points_today?.attributes.bonus_done || []),
      ...(S.points_today?.attributes.pending || []).map((p) => p.name),
    ];
    const match = this._matcher(attrs.chore_ids || {});
    const rows = [];
    for (const [name, pts] of Object.entries(attrs.bonus_chores || {})) {
      const t = match.take(name);
      const ms = t?.actionable ? t : null;
      // A chore that exists in Maintenance Supporter is only shown while it matches the filters.
      // Done or held today it is hidden, linked to a task or not.
      if (t && !ms) continue;
      if (doneToday.includes(name)) continue;
      rows.push({ name, pts, ms, done: false, icon: "mdi:star-circle-outline" });
    }
    for (const t of match.rest()) {
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
  description: "Bonus chores with Done buttons for Maintenance Supporter tasks; bonus points are held until today's mandatory chores are done.",
  preview: true,
});
