import { useMemo, useState } from "react";
import {
  Button, Chip, Grid, Group, Menu, MultiSelect, NumberInput, Paper, Select, Stack, Switch, Text, TextInput, Title,
} from "@mantine/core";
import { useDebouncedValue, useLocalStorage } from "@mantine/hooks";
import { IconChevronDown, IconDownload, IconFilterOff, IconListCheck, IconPlayerPlay, IconSearch } from "@tabler/icons-react";
import type { Ctx } from "../App";
import type { Action, Filters, Kind, SortKey } from "../types";
import {
  EMPTY_FILTERS, REACH_OPTIONS, STATUS_LABEL, TIERS, downloadCsv, matches, renderMessage, sortContacts, statusOf, templateLabel,
} from "../lib";
import ContactTable from "./ContactTable";

const TITLES: Record<Kind, string> = { creator: "Creators", journalist: "Journalists", outlet: "Outlets" };

export default function ContactsView({ kind, ctx }: { kind: Kind; ctx: Ctx }) {
  const { data } = ctx;
  const [f, setF] = useLocalStorage<Filters>({ key: `od-filters-${kind}`, defaultValue: EMPTY_FILTERS, getInitialValueInEffect: false });
  const [sort, setSort] = useLocalStorage<{ key: SortKey; dir: "asc" | "desc" }>({
    key: `od-sort-${kind}`, defaultValue: { key: "score", dir: "desc" }, getInitialValueInEffect: false });
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [buildN, setBuildN] = useState<number | string>(Number(data.config.daily_target) || 30);
  const [q] = useDebouncedValue(f.q, 200);
  const filters = { ...EMPTY_FILTERS, ...f, q };
  const set = <K extends keyof Filters>(k: K, v: Filters[K]) => setF((old) => ({ ...EMPTY_FILTERS, ...old, [k]: v }));

  const pool = useMemo(() => data.contacts.filter((c) => c.kind === kind), [data.contacts, kind]);
  const games = useMemo(() => [...new Set(pool.flatMap((c) => c.games))].sort(), [pool]);
  const types = useMemo(() => [...new Set(data.contacts.filter((c) => c.kind === "outlet").map((c) => c.type))].filter(Boolean).sort(), [data.contacts]);

  const rows = useMemo(() => sortContacts(
    pool.filter((c) => matches(c, filters, statusOf(data.status, c.id), data.today)), sort.key, sort.dir, data.status,
  ), [pool, JSON.stringify(filters), sort, data.status, data.today]);

  const selectedRows = rows.filter((c) => selected.has(c.id));
  const target = selectedRows.length ? selectedRows : rows;
  const template = data.templates.find((t) => t.id === ctx.templateFor(kind));

  const bulk = async (action: Action, label: string) => {
    if (!selectedRows.length) return;
    await ctx.log(selectedRows.map((c) => ({ contact_id: c.id, kind: c.kind, name: c.name, action, template: template?.id })),
      `${label}: ${selectedRows.length}`);
    setSelected(new Set());
  };

  const buildToday = async () => {
    const picks = rows.filter((c) => !statusOf(data.status, c.id).status).slice(0, Number(buildN) || 30);
    if (!picks.length) return;
    await ctx.log(picks.map((c) => ({ contact_id: c.id, kind: c.kind, name: c.name, action: "queued" as Action })),
      `Queued ${picks.length} for today — open the Today tab to work through them`);
  };

  const exportCsv = () => {
    const withEmail = target.filter((c) => c.email);
    downloadCsv(`mailmerge_${kind}_${data.today}.csv`,
      ["id", "name", "email", "subject", "body", "game", "evidence_url", "tier", "fit_score", "route", "links"],
      withEmail.map((c) => {
        const m = renderMessage(template, c, data.config);
        return [c.id, c.name, c.email, m.subject, m.body, c.game, c.evidence[0] || "", c.tier, c.score, c.route,
          c.links.map((l) => l[1]).join(" ")];
      }));
  };

  const activeCount = Object.entries(f).filter(([k, v]) => k !== "status" && k !== "hideDead" && (Array.isArray(v) ? v.length : v !== "" && v !== false)).length;

  return (
    <Grid gutter="md">
      <Grid.Col span={{ base: 12, md: 3 }}>
        <Paper withBorder p="md" radius="md" pos="sticky" top={76}>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text fw={700}>Filters</Text>
              {activeCount > 0 && <Button size="compact-xs" variant="subtle" leftSection={<IconFilterOff size={14} />}
                onClick={() => setF(EMPTY_FILTERS)}>Reset</Button>}
            </Group>
            <TextInput leftSection={<IconSearch size={16} />} placeholder="Name, game, note, email…" value={f.q}
              onChange={(e) => set("q", e.currentTarget.value)} />
            <div>
              <Text size="xs" c="dimmed" mb={4}>Tier</Text>
              <Chip.Group multiple value={f.tiers} onChange={(v) => set("tiers", v)}>
                <Group gap={6}>{TIERS.map((t) => <Chip key={t} value={t} size="xs">{t}</Chip>)}</Group>
              </Chip.Group>
            </div>
            <Select label="Status" value={f.status} onChange={(v) => set("status", v ?? "")} allowDeselect={false}
              data={[{ value: "any", label: "Any status" }, ...Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label })),
                { value: "awaiting", label: "Awaiting reply" }, { value: "due", label: "Follow-up due" }, { value: "positive", label: "Any positive reply" }]} />
            <MultiSelect label="Reach by" description="Only people you can message this way; Message them uses it"
              data={REACH_OPTIONS} value={filters.reach} onChange={(v) => set("reach", v)} clearable placeholder="Any channel" />
            <Switch label="Hide dead ends (no direct contact)" checked={filters.hideDead} onChange={(e) => set("hideDead", e.currentTarget.checked)} />
            <MultiSelect label="Games covered" data={games} value={f.games} onChange={(v) => set("games", v)} searchable clearable placeholder="Any" />
            {kind === "creator" ? (
              <>
                <Group grow gap="xs">
                  <NumberInput label="Min subs" value={f.minSubs} onChange={(v) => set("minSubs", v === "" ? "" : Number(v))} thousandSeparator="," min={0} hideControls />
                  <NumberInput label="Max subs" value={f.maxSubs} onChange={(v) => set("maxSubs", v === "" ? "" : Number(v))} thousandSeparator="," min={0} hideControls />
                </Group>
                <NumberInput label="Active within (days)" value={f.activeDays} onChange={(v) => set("activeDays", v === "" ? "" : Number(v))} min={0} />
                <Switch label="High priority only" checked={f.hp} onChange={(e) => set("hp", e.currentTarget.checked)} />
                <Switch label="Has Twitch" checked={f.twitch} onChange={(e) => set("twitch", e.currentTarget.checked)} />
              </>
            ) : (
              <>
                <MultiSelect label="Outlet type" data={types} value={f.types} onChange={(v) => set("types", v)} clearable placeholder="Any" />
                <Switch label="Writes Next Fest roundups" checked={f.nextfest} onChange={(e) => set("nextfest", e.currentTarget.checked)} />
              </>
            )}
            <NumberInput label="Min fit score" value={f.minScore} onChange={(v) => set("minScore", v === "" ? "" : Number(v))} min={0} max={100} />
          </Stack>
        </Paper>
      </Grid.Col>

      <Grid.Col span={{ base: 12, md: 9 }}>
        <Stack gap="sm">
          <Group justify="space-between" align="flex-end">
            <div>
              <Title order={3}>{TITLES[kind]}</Title>
              <Text size="sm" c="dimmed">{rows.length} shown · {rows.filter((c) => c.email).length} with email
                {selectedRows.length > 0 && ` · ${selectedRows.length} selected`}</Text>
            </div>
            <Group gap="xs">
              <Select size="xs" w={190} label="Message template" allowDeselect={false}
                data={data.templates.map((t) => ({ value: t.id, label: templateLabel(t.id) }))}
                value={ctx.templateFor(kind)} onChange={(v) => v && ctx.setTemplateFor(kind, v)} />
              <NumberInput size="xs" w={70} label="List size" value={buildN} onChange={setBuildN} min={1} max={500} />
              <Button size="xs" leftSection={<IconListCheck size={16} />} onClick={buildToday}
                title="Queue the top N not-yet-contacted rows from this filtered view">Build today's list</Button>
              <Button size="xs" variant="light" leftSection={<IconPlayerPlay size={16} />} disabled={!rows.length}
                onClick={() => ctx.open(rows[0].id, rows.map((c) => c.id))}>Work through</Button>
              <Menu position="bottom-end" withinPortal>
                <Menu.Target>
                  <Button size="xs" variant="default" rightSection={<IconChevronDown size={14} />}>
                    {selectedRows.length ? `Selected (${selectedRows.length})` : "More"}
                  </Button>
                </Menu.Target>
                <Menu.Dropdown>
                  <Menu.Label>Selected rows</Menu.Label>
                  <Menu.Item disabled={!selectedRows.length} onClick={() => bulk("queued", "Queued")}>Queue for today</Menu.Item>
                  <Menu.Item disabled={!selectedRows.length} onClick={() => bulk("contacted", "Marked contacted")}>Mark contacted</Menu.Item>
                  <Menu.Item disabled={!selectedRows.length} onClick={() => bulk("skip", "Skipped")}>Skip</Menu.Item>
                  <Menu.Item disabled={!selectedRows.length} onClick={() => setSelected(new Set())}>Clear selection</Menu.Item>
                  <Menu.Divider />
                  <Menu.Label>{selectedRows.length ? "Selected" : "All shown"} rows</Menu.Label>
                  <Menu.Item leftSection={<IconDownload size={14} />} onClick={exportCsv}>Export mail-merge CSV</Menu.Item>
                  <Menu.Item onClick={() => navigator.clipboard.writeText(target.filter((c) => c.email).map((c) => c.email).join(", "))}>
                    Copy email addresses
                  </Menu.Item>
                </Menu.Dropdown>
              </Menu>
            </Group>
          </Group>
          <ContactTable rows={rows} status={data.status} via={filters.reach} onOpen={(id) => ctx.open(id, rows.map((c) => c.id))}
            selected={selected} onSelect={setSelected} sort={sort}
            onSort={(key) => setSort((s) => ({ key, dir: s.key === key && s.dir === "desc" ? "asc" : "desc" }))} />
        </Stack>
      </Grid.Col>
    </Grid>
  );
}
