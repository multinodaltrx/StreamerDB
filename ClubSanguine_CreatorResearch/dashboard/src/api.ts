import type { LogEntry, Payload, Status } from "./types";

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
  return j as T;
}

export async function fetchData(): Promise<Payload> {
  const r = await fetch("/api/data");
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

/** Append one or more rows to outreach/outreach_log.csv; returns the recomputed statuses. */
export async function logActions(entries: LogEntry[]): Promise<Record<string, Status>> {
  const j = await postJson<{ status: Record<string, Status> }>("/api/log", { entries });
  return j.status;
}

export async function saveRevealedEmail(contact_id: string, email: string): Promise<void> {
  await postJson("/api/reveal", { contact_id, email });
}

/** Open a Gmail compose URL in the Chrome profile signed in as config.gmail_account (server-side launch). */
export async function openMailInProfile(url: string): Promise<void> {
  await postJson("/api/open_mail", { url });
}

/** Reveal the press kit PDF in Explorer so it can be dragged into the compose window. */
export async function showPressKit(): Promise<void> {
  await postJson("/api/show_press_kit", {});
}

/** Reveal the 1080p trailer MP4 in Explorer (too big to attach to Gmail; upload it and share the link). */
export async function showTrailer(): Promise<void> {
  await postJson("/api/show_trailer", {});
}

/** Open a YouTube link in the Chrome profile signed in as config.gmail_account (needed to reveal gated business emails). */
export async function openYoutubeInProfile(url: string): Promise<void> {
  await postJson("/api/open_url", { url });
}
