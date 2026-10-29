import { kcpEsc, kcpT, kcpSensors } from "../helpers.js";
import { KidChoresStatusCardEditor } from "./status.js";

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
  undo: ["mdi:undo-variant", "#8e8e93"],
  medal: ["mdi:medal", "#ffd60a"],
  grace: ["mdi:shield-half-full", "#ff9f0a"],
};

class KidChoresHistoryCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._shown = 0;
    this._confirm = null; // id of the entry awaiting confirmation
    this._error = "";
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
    const sig = [h.language, st?.last_updated, st?.state, this._confirm, this._error].join("|");
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
      const asking = this._confirm === r.id;
      const side = asking
        ? `<div class="btns"><button class="yes" data-id="${kcpEsc(r.id)}">${kcpEsc(kcpT(h, "yes"))}</button><button class="no">${kcpEsc(kcpT(h, "no"))}</button></div>`
        : r.can_revert
        ? `<button class="rev" data-id="${kcpEsc(r.id)}" title="${kcpEsc(kcpT(h, "h_revert"))}" aria-label="${kcpEsc(kcpT(h, "h_revert"))}"><ha-icon icon="mdi:undo-variant"></ha-icon></button>`
        : "";
      const note = asking
        ? `<div class="sub ask">${kcpEsc(kcpT(h, "h_revert_q", { l: label || kcpT(h, "h_no_reason") }))}</div>`
        : r.reverted
        ? `<div class="sub">${kcpEsc(kcpT(h, "h_reverted"))}</div>`
        : "";
      body += `
        <div class="row${r.reverted ? " reverted" : ""}">
          <div class="dot" style="--c:${color}"><ha-icon icon="${icon}"></ha-icon></div>
          <div class="main">
            <div class="lbl">${kcpEsc(label)}</div>
            <div class="sub">${kcpEsc(sub)}</div>
            ${note}
            ${balances ? `<div class="sub">${kcpEsc(kcpT(h, r.week_bonus ? "h_balances_bonus" : "h_balances", { w: r.week, x: r.week_bonus, b: r.bank }) + (r.wallet !== undefined && S?.wallet?.attributes.enabled ? ` · ${kcpT(h, "wallet_title")} ${r.wallet} ${cur}` : ""))}</div>` : ""}
          </div>
          <div class="pts ${cls}">${r.type === "medal" && !pts ? "" : `${sign}${pts} ${kcpEsc(unit)}${kcpEsc(where)}`}${gain ? `<div class="gain">${kcpEsc(gain)}</div>` : ""}</div>
          ${side}
        </div>`;
    }
    const error = this._error ? `<div class="err">${kcpEsc(this._error)}</div>` : "";
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
        .row.reverted .main, .row.reverted .pts { opacity: .5; }
        .row.reverted .lbl, .row.reverted .pts { text-decoration: line-through; }
        .sub.ask { color: var(--primary-text-color); font-weight: 500; }
        .rev { flex: none; width: 32px; height: 32px; padding: 0; border: 0; border-radius: 50%;
          display: grid; place-items: center; background: transparent; cursor: pointer;
          color: var(--secondary-text-color); --mdc-icon-size: 18px; }
        .rev:hover { background: var(--secondary-background-color, rgba(127,127,127,.15)); }
        .btns { display: flex; gap: 6px; flex: none; }
        .btns button { border: 0; border-radius: 8px; padding: 6px 10px; font: inherit; cursor: pointer; }
        .yes { background: var(--primary-color); color: var(--text-primary-color, #fff); }
        .no { background: transparent; color: var(--secondary-text-color); }
        .err { margin: 8px 0; color: var(--error-color, #ff453a); }
        .more { width: 100%; margin-top: 12px; padding: 10px; border: 1px solid var(--divider-color, #888);
          border-radius: 10px; background: transparent; font: inherit; cursor: pointer;
          color: var(--primary-text-color); }
      </style>
      <ha-card>
        <div class="t">${kcpEsc(cfg.title ?? kcpT(h, "history_title"))}</div>
        ${error}${body}${more}
      </ha-card>`;
    const ask = (id) => {
      this._confirm = id;
      this._error = "";
      this._sig = "";
      this._render();
    };
    this.shadowRoot.querySelectorAll(".rev").forEach((b) =>
      b.addEventListener("click", () => ask(b.dataset.id))
    );
    this.shadowRoot.querySelector(".no")?.addEventListener("click", () => ask(null));
    this.shadowRoot.querySelector(".yes")?.addEventListener("click", async (ev) => {
      const id = ev.currentTarget.dataset.id;
      this._confirm = null;
      try {
        await h.callService("kid_chores_points", "revert", {
          id,
          config_entry: (S.points_bank || S.points_week).attributes.entry_id,
        });
      } catch (err) {
        this._error = kcpT(h, "failed", { e: err?.message || err });
      }
      this._sig = "";
      this._render();
    });
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
