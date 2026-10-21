import { kcpEsc, kcpT, kcpSensors } from "../helpers.js";
import { KidChoresStatusCardEditor } from "./status.js";

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
                <div class="big">${parseInt(w?.state, 10) || 0} ${kcpEsc(cur)}</div>
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
