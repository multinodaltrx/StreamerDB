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
