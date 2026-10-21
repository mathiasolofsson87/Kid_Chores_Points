import { kcpEsc, kcpT, kcpSensors } from "../helpers.js";

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
          tasks.push({ id: t.id, name: t.name, entity: t.sensor_entity_id, status: t.status, actionable: labelOk && statuses.includes(t.status) });
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

  /* Pairs chores with Maintenance Supporter tasks: by task id when the chore is linked
   * to one (so renaming the task doesn't break it), otherwise by name. */
  _matcher(ids) {
    const byName = new Map(this._tasks.map((t) => [t.name, t]));
    const byId = new Map(this._tasks.filter((t) => t.id).map((t) => [t.id, t]));
    const left = new Set(byName.values());
    return {
      take: (name) => {
        const t = (ids[name] && byId.get(ids[name])) || byName.get(name);
        if (t) left.delete(t);
        return t;
      },
      rest: () => [...left],
    };
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
    const match = this._matcher(attrs.chore_ids || {});
    const rows = [];
    // done chores are not listed
    for (const name of attrs.remaining || []) {
      const t = match.take(name);
      // A chore that exists in Maintenance Supporter is only shown while it matches the filters.
      if (t && !t.actionable) continue;
      rows.push({ name, done: false, pts: pts[name], ms: t || null });
    }
    for (const t of match.rest()) {
      if (t.actionable) rows.push({ name: t.name, done: false, ms: t });
    }
    return rows.filter((r, i, all) => all.findIndex((x) => x.name === r.name) === i);
  }

  _render() {
    const h = this._hass, cfg = this._config;
    if (!h || !cfg) return;
    const rows = this._rows();
    if (rows) for (const r of rows) r.notes = this._notes.get(r.ms?.name || r.name) || "";
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
  description: "Today's open mandatory chores, one per line, plus Done buttons for the matching Maintenance Supporter tasks.",
  preview: true,
});

export { KidChoresTodoCard, KidChoresTodoCardEditor };
