export type Kind = "creator" | "journalist" | "outlet";

export interface Contact {
  id: string;
  kind: Kind;
  name: string;
  tier: string;
  score: number;
  hp: boolean;
  subs: number | null;
  twitch: boolean;
  games: string[];
  game: string;
  evidence: string[];
  links: [string, string][];
  email: string;
  email_revealed: boolean;
  route: string;
  last_active: string;
  country: string;
  style: string;
  type: string;
  outlet: string;
  nextfest?: string;
  notes: string;
  message: { how: "email" | "gated" | "discord" | "form" | "dm" | "web" | "none"; label: string; url: string };
}

export type Action =
  | "queued" | "contacted" | "followed_up" | "replied" | "interested"
  | "key_sent" | "covered" | "declined" | "skip" | "note" | "undo";

export interface HistoryEntry {
  timestamp: string;
  action: Action;
  channel: string;
  template: string;
  note: string;
}

export interface Status {
  status: Action | "";
  since: string;
  follow_up_on: string;
  channel: string;
  history: HistoryEntry[];
}

export interface Template {
  id: string;
  subject: string;
  body: string;
}

export interface Config {
  game_title?: string;
  my_name?: string;
  gmail_account?: string;
  steam_url?: string;
  press_kit_url?: string;
  trailer_url?: string;
  nextfest?: string;
  nextfest_start?: string;
  demo_note?: string;
  signature?: string;
  daily_target?: number;
  follow_up_days?: number;
  [key: string]: unknown;
}

export interface Payload {
  contacts: Contact[];
  status: Record<string, Status>;
  config: Config;
  templates: Template[];
  today: string;
}

export interface LogEntry {
  contact_id: string;
  kind: Kind;
  name: string;
  action: Action;
  channel?: string;
  template?: string;
  note?: string;
}

export interface Filters {
  q: string;
  tiers: string[];
  status: string;
  routes: string[];
  games: string[];
  types: string[];
  hp: boolean;
  twitch: boolean;
  nextfest: boolean;
  minSubs: number | "";
  maxSubs: number | "";
  minScore: number | "";
  activeDays: number | "";
}

export type SortKey = "score" | "name" | "subs" | "last_active" | "status";
