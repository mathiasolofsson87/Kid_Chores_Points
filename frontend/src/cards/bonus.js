import { kcpEsc, kcpT, kcpSensors } from "../helpers.js";
import { KidChoresTodoCard, KidChoresTodoCardEditor } from "./todo.js";

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
    const match = this._matcher(attrs.chore_ids || {});
    const rows = [];
    for (const [name, pts] of Object.entries(attrs.bonus_chores || {})) {
      const t = match.take(name);
      const ms = t?.actionable ? t : null;
      // A chore that exists in Maintenance Supporter is only shown while it matches the filters;
      // one that was already done today is not shown (unless it is due again).
      if (t && !ms) continue;
      if (!ms && doneToday.includes(name)) continue;
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
  description: "Bonus chores with Done buttons for Maintenance Supporter tasks; locked until today's mandatory chores are done.",
  preview: true,
});
