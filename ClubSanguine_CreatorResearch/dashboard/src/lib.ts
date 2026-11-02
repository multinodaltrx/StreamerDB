import { openMailInProfile, openYoutubeInProfile } from "./api";
import type { Config, Contact, Filters, How, Route, SortKey, Status, Template } from "./types";

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
/** Statuses that mean an introduction already went out, so no second intro on any channel. */
export const INTRODUCED = ["contacted", "followed_up", "replied", "interested", "key_sent", "covered"];

export const HOW_LABEL: Record<How, string> = {
  email: "Email", gated: "Gated email", discord: "Discord", form: "Form", dm: "Social DM", web: "Website only", none: "None",
};
export const REACH_OPTIONS = (["email", "discord", "dm", "form", "gated"] as How[]).map((value) => ({ value, label: HOW_LABEL[value] }));
const isDead = (r: Route) => r.how === "web" || r.how === "none";
export const AWAITING = ["contacted", "followed_up"];

export const EMPTY_FILTERS: Filters = {
  q: "", tiers: [], status: "", routes: [], reach: [], hideDead: true, games: [], types: [],
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
  if (f.reach?.length && !c.reach.some((r) => f.reach.includes(r.how))) return false;
  if (f.hideDead && c.reach.every(isDead)) return false;
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

/** Template that fits who they are, how they're being reached and where things stand.
 *  Mirrors default_template() in tools/outreach_app.py. */
export function defaultTemplateId(c: Contact, how: How, status = ""): string {
  if (status === "contacted" || status === "followed_up") return "5_follow_up";
  if (c.kind !== "creator") return status === "replied" || status === "interested" ? "7_send_press_kit" : "3_press_pitch";
  if (status === "replied" || status === "interested") return ["discord", "dm", "form"].includes(how) ? "8_dm_steam_link" : "1_creator_email";
  return how === "email" || how === "gated" ? "1_creator_email" : "2_creator_dm";
}

/** Route to message them on: the first channel picked in the list's "Reach by" filter, else the best one. */
export function preferredRoute(c: Contact): Route {
  let want: string[] = [];
  try { want = JSON.parse(localStorage.getItem(`od-filters-${c.kind}`) || "{}").reach || []; } catch { /* storage blocked */ }
  return c.reach.find((r) => want.includes(r.how)) || c.reach[0] || c.message;
}

/** Channel name for the log, from the route being used. */
export function logChannel(r: Route): string {
  if (r.how === "email" || r.how === "gated") return "email";
  if (r.how === "discord" || r.how === "form") return r.how;
  if (/(x|twitter)\.com/i.test(r.url)) return "x";
  if (/bsky\.app/i.test(r.url)) return "bluesky";
  return "other";
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
    seen_line: seenLine(c),
    coverage_line: coverageLine(c),
  };
  return text.replace(/\{(\w+)\}/g, (m, k) => {
    const v = vars[k];
    return v !== undefined && (v !== "" || k.endsWith("_line")) ? String(v) : m;
  }).replace(/\n{3,}/g, "\n\n");
}

/** One verified, specific thing about a creator's channel. Never claims the owner watched it. */
function seenLine(c: Contact): string {
  if (c.evidence_title) return `I noticed your video "${c.evidence_title}"`;
  if (c.game) return `I noticed you've played ${c.game} on your channel`;
  return "I came across your channel while looking for people who play deduction games";
}

function coverageLine(c: Contact): string {
  if (!c.game) return "";
  return ` I saw ${c.kind === "journalist" ? "you've written about" : "you've covered"} ${c.game}, which is why I thought of you.`;
}

/** Placeholders still unfilled in a message, e.g. {steam_url} while config is blank. */
export function unfilled(text: string): string[] {
  return [...new Set(text.match(/\{\w+\}/g) || [])];
}

export function renderMessage(t: Template | undefined, c: Contact, config: Config) {
  if (!t) return { subject: "", body: "" };
  return { subject: fillTemplate(t.subject, c, config), body: fillTemplate(t.body, c, config) };
}

/** When set (config.gmail_account), email links open a Gmail compose window for that account instead of the default mail app. */
let gmailAccount = "";
export function setGmailAccount(a: string | undefined) { gmailAccount = (a || "").trim(); }
export function getGmailAccount() { return gmailAccount; }

/** Every Gmail account the owner can send from: config.gmail_account first, then config.gmail_accounts. */
export function senderOptions(config: Config): string[] {
  return [...new Set([config.gmail_account, ...(config.gmail_accounts || [])].map((a) => (a || "").trim()).filter(Boolean))];
}

/** Major outlets, Arabic-language press and IGN go out from config.press_major_account; everyone else from config.gmail_account.
 * Mirrors tools/outreach_app.py default_sender. */
export function defaultSender(c: Contact, config: Config): string {
  const major = (config.press_major_account || "").trim();
  if (major && c.kind !== "creator"
    && (/major outlet/i.test(c.type) || /arab/i.test(c.country) || /\bIGN\b/.test(`${c.name} ${c.outlet}`))) return major;
  return (config.gmail_account || "").trim();
}

export function mailtoHref(email: string, subject: string, body: string, from = gmailAccount): string {
  if (from) {
    return `https://mail.google.com/mail/?view=cm&fs=1&authuser=${encodeURIComponent(from)}&to=${encodeURIComponent(email)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  }
  return `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

/** Open the compose window: Gmail via the server (Chrome profile signed in as `from`), else the browser/default mail app. */
export function openMail(email: string, subject: string, body: string, from = gmailAccount) {
  const href = mailtoHref(email, subject, body, from);
  if (!from) { window.open(href, "_blank", "noopener"); return; }
  openMailInProfile(href).catch(() => window.open(href, "_blank", "noopener"));
}

export const isYoutube = (url: string) => /^https?:\/\/(www\.)?youtube\.com\//i.test(url);

/** Open a link: YouTube goes through the signed-in Chrome profile when one is configured, everything else in a new tab. */
export function openLink(url: string) {
  const www = url.replace("://youtube.com", "://www.youtube.com");
  if (gmailAccount && isYoutube(url)) { openYoutubeInProfile(www).catch(() => window.open(www, "_blank", "noopener")); return; }
  window.open(isYoutube(url) ? www : url, "_blank", "noopener");
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
