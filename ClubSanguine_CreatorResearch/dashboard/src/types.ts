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
  /** Submission rules / contact preference on record (press only). */
  policy: string;
  /** Title of a verified evidence video, quoted in creator drafts. */
  evidence_title: string;
  /** Best route; same as reach[0]. */
  message: Route;
  /** Every channel this contact can be messaged on, best first. */
  reach: Route[];
}

export type How = "email" | "gated" | "discord" | "form" | "dm" | "web" | "none";
export interface Route { how: How; label: string; url: string }

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
  /** Extra accounts selectable as "Send from". */
  gmail_accounts?: string[];
  /** Default sender for major outlets, Arabic press and IGN. */
  press_major_account?: string;
  steam_url?: string;
  press_kit_url?: string;
  press_kit_file?: string;
  trailer_file?: string;
  trailer_url?: string;
  nextfest?: string;
  nextfest_start?: string;
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
  /** Only contacts reachable on one of these channels (Route.how). */
  reach: string[];
  /** Hide contacts with no direct way to message them (website only / nothing). */
  hideDead: boolean;
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
