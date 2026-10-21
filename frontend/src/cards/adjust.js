import { kcpEsc, kcpT, kcpSensors } from "../helpers.js";
import { KidChoresStatusCardEditor } from "./status.js";

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
