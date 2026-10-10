import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionIcon, Alert, AppShell, Badge, Burger, Center, Code, Group, Loader, NavLink,
  RingProgress, Text, Title, Tooltip, useMantineColorScheme,
} from "@mantine/core";
import { useDisclosure, useLocalStorage } from "@mantine/hooks";
import { notifications } from "@mantine/notifications";
import {
  IconAlertTriangle, IconBell, IconBuildingBroadcastTower, IconCalendarCheck, IconLayoutKanban,
  IconMoon, IconNews, IconRefresh, IconSun, IconUsers,
} from "@tabler/icons-react";
import { fetchData, logActions, saveRevealedEmail } from "./api";
import type { Contact, Kind, LogEntry, Payload } from "./types";
import { actedToday, defaultTemplateId, isFollowUpDue, messagedToday, statusOf } from "./lib";
import ContactsView from "./components/ContactsView";
import TodayView from "./components/TodayView";
import PipelineView from "./components/PipelineView";
import ContactDrawer from "./components/ContactDrawer";

export type Section = Kind | "today" | "followups" | "pipeline";

export interface Ctx {
  data: Payload;
  log: (entries: LogEntry[], toast?: string) => Promise<void>;
  reveal: (c: Contact, email: string) => Promise<void>;
  open: (id: string, queue: string[]) => void;
  templateFor: (kind: Kind) => string;
  setTemplateFor: (kind: Kind, id: string) => void;
}

const NAV: { key: Section; label: string; icon: typeof IconUsers; group: string }[] = [
  { key: "creator", label: "Streamers & YouTubers", icon: IconUsers, group: "Streamers" },
  { key: "journalist", label: "Journalists", icon: IconNews, group: "Press" },
  { key: "outlet", label: "Outlets", icon: IconBuildingBroadcastTower, group: "Press" },
  { key: "today", label: "Today", icon: IconCalendarCheck, group: "My outreach" },
  { key: "followups", label: "Follow-ups", icon: IconBell, group: "My outreach" },
  { key: "pipeline", label: "Pipeline", icon: IconLayoutKanban, group: "My outreach" },
];

export default function App() {
  const [data, setData] = useState<Payload | null>(null);
  const [error, setError] = useState("");
  const [section, setSection] = useLocalStorage<Section>({ key: "od-section", defaultValue: "creator" });
  const [tpl, setTpl] = useLocalStorage<Record<string, string>>({ key: "od-templates", defaultValue: {} });
  const [drawer, setDrawer] = useState<{ id: string; queue: string[] } | null>(null);
  const [navOpen, { toggle: toggleNav, close: closeNav }] = useDisclosure(false);
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();

  const reload = useCallback(async () => {
    try { setData(await fetchData()); setError(""); }
    catch (e) { setError(String(e)); }
  }, []);
  useEffect(() => { reload(); }, [reload]);
  // Deep link: http://127.0.0.1:8765/#C0002 opens that contact.
  useEffect(() => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (data && id && data.contacts.some((c) => c.id === id)) setDrawer({ id, queue: [id] });
  }, [data === null]);

  const ctx: Ctx | null = useMemo(() => data && {
    data,
    log: async (entries, toast) => {
      try {
        const status = await logActions(entries);
        setData((d) => d && { ...d, status });
        if (toast) notifications.show({ message: toast, color: "teal", autoClose: 1600 });
      } catch (e) {
        notifications.show({ title: "Not saved", message: String(e), color: "red" });
      }
    },
    reveal: async (c, email) => {
      await saveRevealedEmail(c.id, email);
      notifications.show({ message: `Saved email for ${c.name}`, color: "teal", autoClose: 1600 });
      await reload();
    },
    open: (id, queue) => setDrawer({ id, queue }),
    templateFor: (kind) => tpl[kind === "creator" ? "creator" : "press"] || defaultTemplateId(kind),
    setTemplateFor: (kind, id) => setTpl((t) => ({ ...t, [kind === "creator" ? "creator" : "press"]: id })),
  }, [data, tpl, reload, setTpl]);

  if (error && !data) {
    return <Center h="100vh"><Alert color="red" title="Can't reach the outreach server">
      Start it with <Code>python tools/outreach_app.py</Code>, then reload. ({error})</Alert></Center>;
  }
  if (!data || !ctx) return <Center h="100vh"><Loader /></Center>;

  const today = data.today;
  const statuses = data.contacts.map((c) => statusOf(data.status, c.id));
  const counts: Record<string, number> = {
    creator: data.contacts.filter((c) => c.kind === "creator").length,
    journalist: data.contacts.filter((c) => c.kind === "journalist").length,
    outlet: data.contacts.filter((c) => c.kind === "outlet").length,
    today: statuses.filter((s) => actedToday(s, today)).length,
    followups: statuses.filter((s) => isFollowUpDue(s, today)).length,
    pipeline: statuses.filter((s) => s.status).length,
  };
  const done = statuses.filter((s) => messagedToday(s, today)).length;
  const target = Number(data.config.daily_target) || 30;
  const missing = ["steam_url", "press_kit_url"].filter((k) => !data.config[k]);
  const fest = data.config.nextfest_start
    ? Math.ceil((Date.parse(String(data.config.nextfest_start)) - Date.parse(today)) / 864e5) : null;

  return (
    <AppShell header={{ height: 60 }} navbar={{ width: 220, breakpoint: "sm", collapsed: { mobile: !navOpen } }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <Burger opened={navOpen} onClick={toggleNav} hiddenFrom="sm" size="sm" />
            <Title order={4}>Outreach Desk</Title>
            <Badge variant="light" visibleFrom="xs">{String(data.config.game_title || "Club Sanguine")}</Badge>
            {fest != null && fest >= 0 && <Badge color="grape" variant="dot" visibleFrom="md">Next Fest in {fest} days</Badge>}
          </Group>
          <Group gap="xs" wrap="nowrap">
            <Tooltip label={`Messaged today: ${done} of ${target}`}>
              <Group gap={6} wrap="nowrap">
                <RingProgress size={40} thickness={5} roundCaps
                  sections={[{ value: Math.min(100, (done / target) * 100), color: done >= target ? "teal" : "wine" }]} />
                <Text size="sm" fw={600} visibleFrom="xs">{done}/{target}</Text>
              </Group>
            </Tooltip>
            <Tooltip label="Reload data from disk"><ActionIcon variant="default" size="lg" onClick={reload}><IconRefresh size={18} /></ActionIcon></Tooltip>
            <Tooltip label="Toggle theme"><ActionIcon variant="default" size="lg" onClick={toggleColorScheme}>
              {colorScheme === "dark" ? <IconSun size={18} /> : <IconMoon size={18} />}</ActionIcon></Tooltip>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="xs">
        {NAV.map((n, i) => (
          <div key={n.key}>
          {(i === 0 || NAV[i - 1].group !== n.group) && (
            <Text size="xs" fw={700} c="dimmed" tt="uppercase" px="sm" mt={i ? "md" : 4} mb={4}>{n.group}</Text>
          )}
          <NavLink active={section === n.key} label={n.label} leftSection={<n.icon size={18} />}
            rightSection={counts[n.key] ? <Badge size="sm" variant={n.key === "followups" ? "filled" : "light"}
              color={n.key === "followups" ? "orange" : undefined}>{counts[n.key]}</Badge> : null}
            onClick={() => { setSection(n.key); closeNav(); }} style={{ borderRadius: 8 }} />
          </div>
        ))}
        <Text size="xs" c="dimmed" mt="auto" p="xs">Nothing is ever sent from here. You message people yourself, and every click is logged to <Code>outreach_log.csv</Code>.</Text>
      </AppShell.Navbar>

      <AppShell.Main>
        {missing.length > 0 && (
          <Alert icon={<IconAlertTriangle />} color="yellow" mb="md" variant="light">
            Set <b>{missing.join(", ")}</b> in <Code>outreach/config.json</Code> so messages include your links, then press reload.
          </Alert>
        )}
        {(section === "creator" || section === "journalist" || section === "outlet") && <ContactsView key={section} kind={section} ctx={ctx} />}
        {(section === "today" || section === "followups") && <TodayView key={section} mode={section} ctx={ctx} goTo={setSection} />}
        {section === "pipeline" && <PipelineView ctx={ctx} />}
      </AppShell.Main>

      <ContactDrawer ctx={ctx} state={drawer} onNavigate={(id) => drawer && setDrawer({ ...drawer, id })} onClose={() => setDrawer(null)} />
    </AppShell>
  );
}
