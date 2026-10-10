import type { Config, Contact, Filters, Kind, SortKey, Status, Template } from "./types";

export const STATUS_LABEL: Record<string, string> = {
  "": "Not contacted",
  queued: "Queued",
  contacted: "Contacted",
  followed_up: "Followed up",
  replied: "Replied",
  interested: "Interested",
  key_sent: "Key sent",
  covered: "Covered",
  declined: "Declined",
  skip: "Skipped",
};

export const STATUS_COLOR: Record<string, string> = {
  "": "gray",
  queued: "violet",
  contacted: "yellow",
  followed_up: "orange",
  replied: "teal",
  interested: "green",
  key_sent: "cyan",
  covered: "lime",
  declined: "red",
  skip: "gray",
};

export const TIER_COLOR: Record<string, string> = { S: "grape", A: "orange", B: "blue", C: "gray", "Long Tail": "dark" };
export const TIERS = ["S", "A", "B", "C", "Long Tail"];
export const CHANNELS = ["email", "discord", "x", "bluesky", "twitch", "youtube", "form", "other"];
export const POSITIVE = ["replied", "interested", "key_sent", "covered"];
export const AWAITING = ["contacted", "followed_up"];

export const EMPTY_FILTERS: Filters = {
  q: "", tiers: [], status: "", routes: [], games: [], types: [],
  hp: false, twitch: false, nextfest: false,
  minSubs: "", maxSubs: "", minScore: "", activeDays: "",
};

const NO_STATUS: Status = { status: "", since: "", follow_up_on: "", channel: "", history: [] };
export const statusOf = (s: Record<string, Status>, id: string): Status => s[id] || NO_STATUS;

export function daysBetween(fromIso: string, toIso: string): number | null {
  if (!fromIso) return null;
  const d = (Date.parse(toIso) - Date.parse(fromIso.slice(0, 10))) / 864e5;
  return Number.isFinite(d) ? Math.round(d) : null;
}

export function fmtSubs(n: number | null): string {
  if (n == null) return "—";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(n >= 1e4 ? 0 : 1) + "K";
  return String(n);
}

export function isFollowUpDue(st: Status, today: string): boolean {
  return AWAITING.includes(st.status) && !!st.follow_up_on && st.follow_up_on <= today;
}

export function actedToday(st: Status, today: string): boolean {
  return st.history.some((h) => h.timestamp.startsWith(today));
}

export function messagedToday(st: Status, today: string): boolean {
  // current (post-undo) status only, so an undone "contacted" no longer counts
  return AWAITING.includes(st.status) && st.since === today;
}

export function matches(c: Contact, f: Filters, st: Status, today: string): boolean {
  if (f.q) {
    const hay = `${c.name} ${c.games.join(" ")} ${c.notes} ${c.outlet} ${c.email}`.toLowerCase();
    if (!hay.includes(f.q.toLowerCase())) return false;
  }
  if (f.tiers.length && !f.tiers.includes(c.tier)) return false;
  if (f.status !== "any") {
    if (f.status === "awaiting") { if (!AWAITING.includes(st.status)) return false; }
    else if (f.status === "positive") { if (!POSITIVE.includes(st.status)) return false; }
    else if (f.status === "due") { if (!isFollowUpDue(st, today)) return false; }
    else if (st.status !== f.status) return false;
  }
  if (f.routes.length && !f.routes.includes(c.route)) return false;
  if (f.games.length && !f.games.some((g) => c.games.includes(g))) return false;
  if (f.types.length && !f.types.some((t) => c.type.includes(t))) return false;
  if (f.hp && !c.hp) return false;
  if (f.twitch && !c.twitch) return false;
  if (f.nextfest && c.nextfest !== "Yes") return false;
  if (f.minSubs !== "" && (c.subs == null || c.subs < f.minSubs)) return false;
  if (f.maxSubs !== "" && (c.subs == null || c.subs > f.maxSubs)) return false;
  if (f.minScore !== "" && c.score < f.minScore) return false;
  if (f.activeDays !== "") {
    const d = daysBetween(c.last_active, today);
    if (d == null || d > f.activeDays) return false;
  }
  return true;
}

export function sortContacts(list: Contact[], key: SortKey, dir: "asc" | "desc", status: Record<string, Status>) {
  const m = dir === "asc" ? 1 : -1;
  const val = (c: Contact): number | string => {
    switch (key) {
      case "name": return c.name.toLowerCase();
      case "subs": return c.subs ?? -1;
      case "last_active": return c.last_active || "";
      case "status": return statusOf(status, c.id).since || "";
      default: return c.score;
    }
  };
  return [...list].sort((a, b) => {
    const va = val(a), vb = val(b);
    if (va < vb) return -1 * m;
    if (va > vb) return 1 * m;
    return b.score - a.score;
  });
}

export function defaultTemplateId(kind: Kind): string {
  return kind === "creator" ? "1_creator_email" : "3_press_pitch";
}

export function templateLabel(id: string): string {
  return id.replace(/^\d+_/, "").replace(/_/g, " ").replace(/^\w/, (s) => s.toUpperCase());
}

export function greetingName(c: Contact): string {
  if (c.kind === "journalist") return c.name.split(/\s+/)[0];
  if (c.kind === "outlet") return `${c.name} team`;
  return c.name;
}

export function fillTemplate(text: string, c: Contact, config: Config): string {
  const vars: Record<string, unknown> = {
    ...config,
    name: greetingName(c),
    full_name: c.name,
    game: c.game || "indie horror",
    games: c.games.join(", "),
    evidence_url: c.evidence[0] || "",
    outlet: c.outlet,
  };
  return text.replace(/\{(\w+)\}/g, (m, k) => {
    const v = vars[k];
    return v !== undefined && v !== "" ? String(v) : m;
  });
}

/** Placeholders still unfilled in a message, e.g. {steam_url} while config is blank. */
export function unfilled(text: string): string[] {
  return [...new Set(text.match(/\{\w+\}/g) || [])];
}

export function renderMessage(t: Template | undefined, c: Contact, config: Config) {
  if (!t) return { subject: "", body: "" };
  return { subject: fillTemplate(t.subject, c, config), body: fillTemplate(t.body, c, config) };
}

export function mailtoHref(email: string, subject: string, body: string): string {
  return `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

export function defaultChannel(c: Contact): string {
  if (c.email) return "email";
  const labels = c.links.map((l) => l[0].toLowerCase()).join(" ");
  if (labels.includes("discord")) return "discord";
  if (labels.includes("submit")) return "form";
  return "x";
}

export function downloadCsv(filename: string, header: string[], rows: (string | number)[][]) {
  const q = (v: string | number) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const text = "﻿" + [header, ...rows].map((r) => r.map(q).join(",")).join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
