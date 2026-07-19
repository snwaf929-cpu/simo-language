"""Static browser runtime and base CSS for Simo builds."""

_BASE_CSS = """\
:root {
  color-scheme: light dark;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f5f6f8;
  color: #17191c;
}
* { box-sizing: border-box; }
html, body { margin: 0; min-height: 100%; }
body { min-height: 100vh; background: #f5f6f8; }
.simo-shell { min-height: 100vh; display: grid; place-items: center; padding: 32px 18px; }
.simo-app {
  width: min(100%, 960px);
  min-height: 240px;
  padding: 32px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 22px;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.10);
}
.simo-app > * { max-width: 100%; }
h1, h2, h3, p { margin-top: 0; }
button, input {
  font: inherit;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  padding: 11px 15px;
}
button { cursor: pointer; background: #17191c; color: #fff; }
button:hover { transform: translateY(-1px); }
input { width: 100%; background: transparent; color: inherit; }
img { display: block; max-width: 100%; }
.simo-toast {
  position: fixed; right: 20px; bottom: 20px; z-index: 9999;
  padding: 13px 18px; border-radius: 12px; color: white; background: #17191c;
  box-shadow: 0 12px 35px rgba(0,0,0,.22); animation: simo-in .18s ease-out;
}
@keyframes simo-in { from { opacity: 0; transform: translateY(8px); } }
@media (prefers-color-scheme: dark) {
  :root { background: #101113; color: #f1f2f4; }
  body { background: #101113; }
  .simo-app { background: #181a1e; border-color: rgba(255,255,255,.10); }
  button, input { border-color: rgba(255,255,255,.18); }
}
"""


_RUNTIME_JS = r"""
const Simo = {
  text(value) {
    if (value === null || value === undefined) return "null";
    if (value === true) return "true";
    if (value === false) return "false";
    if (Array.isArray(value)) return `[${value.map(Simo.text).join(", ")}]`;
    if (typeof value === "object") {
      return `{${Object.entries(value).map(([k, v]) => `${k}: ${Simo.text(v)}`).join(", ")}}`;
    }
    return String(value);
  },
  number(value) {
    const result = Number(value);
    if (Number.isNaN(result)) throw new Error(`Cannot convert ${value} to a number`);
    return result;
  },
  bool(value) {
    if (typeof value === "string") {
      const normalized = value.trim().toLowerCase();
      if (["true", "yes", "1", "on"].includes(normalized)) return true;
      if (["false", "no", "0", "off", ""].includes(normalized)) return false;
    }
    return Boolean(value);
  },
  len(value) { return value == null ? 0 : Object.keys(value).length; },
  range(...args) {
    let start = 0, stop = 0, step = 1;
    if (args.length === 1) stop = Number(args[0]);
    else if (args.length >= 2) [start, stop, step = 1] = args.map(Number);
    const output = [];
    if (step === 0) throw new Error("range step cannot be zero");
    if (step > 0) for (let i = start; i < stop; i += step) output.push(i);
    else for (let i = start; i > stop; i += step) output.push(i);
    return output;
  },
  add(collection, value) {
    if (!Array.isArray(collection)) throw new Error("add() requires a list");
    collection.push(value); return collection;
  },
  remove(collection, value) {
    if (Array.isArray(collection)) {
      const index = collection.indexOf(value); if (index >= 0) collection.splice(index, 1);
    } else if (collection && typeof collection === "object") delete collection[value];
    return collection;
  },
  contains(collection, value) {
    if (Array.isArray(collection) || typeof collection === "string") return collection.includes(value);
    return collection && typeof collection === "object" ? value in collection : false;
  },
  keys(value) { return value && typeof value === "object" ? Object.keys(value) : []; },
  values(value) { return value && typeof value === "object" ? Object.values(value) : []; },
  iter(value) { return value && typeof value === "object" && !Array.isArray(value) ? Object.keys(value) : (value ?? []); },
  get(value, key) {
    if (value == null) throw new Error(`Cannot read ${key} from null`);
    if (key === "length" && (Array.isArray(value) || typeof value === "string")) return value.length;
    return value[key];
  },
  equal(a, b) {
    if (typeof a === "boolean" || typeof b === "boolean") return typeof a === "boolean" && typeof b === "boolean" && a === b;
    return a === b;
  },
  addValues(a, b) {
    if (typeof a === "string" || typeof b === "string") return Simo.text(a) + Simo.text(b);
    if (Array.isArray(a) && Array.isArray(b)) return [...a, ...b];
    return Number(a) + Number(b);
  },
  notify(value) {
    const toast = document.createElement("div"); toast.className = "simo-toast";
    toast.textContent = Simo.text(value); document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2800);
  },
  assert(condition, message = "Assertion failed") { if (!condition) throw new Error(Simo.text(message)); },
  save(key, value) { localStorage.setItem(String(key), JSON.stringify(value)); return value; },
  load(key, fallback = null) {
    const value = localStorage.getItem(String(key));
    if (value === null) return fallback;
    try { return JSON.parse(value); } catch { return value; }
  }
};
const $el = (id) => document.getElementById(id);
"""
