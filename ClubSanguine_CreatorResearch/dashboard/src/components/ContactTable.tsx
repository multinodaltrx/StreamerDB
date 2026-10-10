import { useEffect, useState } from "react";
import { ActionIcon, Badge, Checkbox, Group, Pagination, Paper, ScrollArea, Select, Table, Text, Tooltip, UnstyledButton } from "@mantine/core";
import { IconChevronDown, IconChevronUp, IconMail, IconSelector, IconStarFilled } from "@tabler/icons-react";
import type { Contact, SortKey, Status } from "../types";
import { STATUS_COLOR, STATUS_LABEL, TIER_COLOR, fmtSubs, statusOf } from "../lib";

interface Props {
  rows: Contact[];
  status: Record<string, Status>;
  onOpen: (id: string) => void;
  selected?: Set<string>;
  onSelect?: (s: Set<string>) => void;
  sort?: { key: SortKey; dir: "asc" | "desc" };
  onSort?: (key: SortKey) => void;
  showKind?: boolean;
  dateLabel?: string;
  dateOf?: (c: Contact) => string;
}

const HOW_LABEL: Record<string, string> = { email: "Email", gated: "Gated email", discord: "Discord", form: "Form", dm: "Social DM", web: "Website", none: "None" };
const HOW_COLOR: Record<string, string> = { email: "teal", gated: "yellow", discord: "indigo", form: "blue", dm: "grape", web: "gray", none: "red" };

export default function ContactTable({ rows, status, onOpen, selected, onSelect, sort, onSort, showKind, dateLabel = "Last active", dateOf }: Props) {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState("50");
  const pp = Number(perPage);
  const pages = Math.max(1, Math.ceil(rows.length / pp));
  useEffect(() => { if (page > pages) setPage(1); }, [pages, page]);
  const visible = rows.slice((page - 1) * pp, page * pp);
  const allOnPage = visible.length > 0 && selected != null && visible.every((c) => selected.has(c.id));

  const Th = ({ k, children, w }: { k?: SortKey; children: React.ReactNode; w?: number }) => {
    if (!k || !onSort || !sort) return <Table.Th w={w}>{children}</Table.Th>;
    const Icon = sort.key === k ? (sort.dir === "asc" ? IconChevronUp : IconChevronDown) : IconSelector;
    return (
      <Table.Th w={w}>
        <UnstyledButton onClick={() => onSort(k)}>
          <Group gap={4} wrap="nowrap"><Text fw={600} size="sm">{children}</Text><Icon size={14} /></Group>
        </UnstyledButton>
      </Table.Th>
    );
  };

  const toggle = (id: string) => {
    if (!selected || !onSelect) return;
    const s = new Set(selected);
    s.has(id) ? s.delete(id) : s.add(id);
    onSelect(s);
  };

  return (
    <Paper withBorder radius="md">
      <ScrollArea>
        <Table highlightOnHover stickyHeader verticalSpacing="xs" miw={860}>
          <Table.Thead>
            <Table.Tr>
              {onSelect && (
                <Table.Th w={36}>
                  <Checkbox size="xs" checked={allOnPage} aria-label="Select page"
                    onChange={() => {
                      const s = new Set(selected);
                      visible.forEach((c) => (allOnPage ? s.delete(c.id) : s.add(c.id)));
                      onSelect(s);
                    }} />
                </Table.Th>
              )}
              <Th k="score" w={70}>Fit</Th>
              <Th k="name">Name</Th>
              {showKind && <Table.Th>Type</Table.Th>}
              <Th k="subs" w={130}>{rows[0]?.kind === "creator" || showKind ? "Size" : "Outlet / type"}</Th>
              <Table.Th>Games</Table.Th>
              <Table.Th w={130}>Contact</Table.Th>
              <Th k="last_active" w={110}>{dateLabel}</Th>
              <Th k="status" w={150}>Status</Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {visible.map((c) => {
              const st = statusOf(status, c.id);
              return (
                <Table.Tr key={c.id} onClick={() => onOpen(c.id)} style={{ cursor: "pointer" }}
                  bg={selected?.has(c.id) ? "var(--mantine-primary-color-light)" : undefined}>
                  {onSelect && (
                    <Table.Td onClick={(e) => e.stopPropagation()}>
                      <Checkbox size="xs" checked={selected!.has(c.id)} onChange={() => toggle(c.id)} aria-label={`Select ${c.name}`} />
                    </Table.Td>
                  )}
                  <Table.Td>
                    <Group gap={6} wrap="nowrap">
                      <Badge size="sm" color={TIER_COLOR[c.tier] || "gray"} variant="filled" w={28} px={0}>{c.tier === "Long Tail" ? "LT" : c.tier || "–"}</Badge>
                      <Text size="sm" c="dimmed">{Math.round(c.score)}</Text>
                    </Group>
                  </Table.Td>
                  <Table.Td>
                    <Group gap={6} wrap="nowrap">
                      {c.hp && <Tooltip label="High priority"><IconStarFilled size={14} color="var(--mantine-color-yellow-6)" /></Tooltip>}
                      <div>
                        <Text size="sm" fw={600} lineClamp={1}>{c.name}</Text>
                        <Text size="xs" c="dimmed">{c.id}{c.country ? ` · ${c.country}` : ""}</Text>
                      </div>
                    </Group>
                  </Table.Td>
                  {showKind && <Table.Td><Text size="sm" tt="capitalize">{c.kind}</Text></Table.Td>}
                  <Table.Td>
                    {c.kind === "creator"
                      ? <Text size="sm">{fmtSubs(c.subs)}{c.twitch && <Badge ml={6} size="xs" color="violet" variant="light">Twitch</Badge>}</Text>
                      : <Text size="sm" lineClamp={2}>{c.kind === "journalist" ? c.outlet : c.type}</Text>}
                  </Table.Td>
                  <Table.Td>
                    <Tooltip label={c.games.join(" · ")} disabled={!c.games.length} multiline maw={360}>
                      <Text size="xs" lineClamp={2} maw={300}>{c.games.join(" · ") || "—"}</Text>
                    </Tooltip>
                  </Table.Td>
                  <Table.Td>
                    <Group gap={4} wrap="nowrap">
                      <Tooltip label={c.message.label}><Badge size="sm" variant="light" color={HOW_COLOR[c.message.how] || "gray"} tt="none">{HOW_LABEL[c.message.how]}</Badge></Tooltip>
                      {c.email && <Tooltip label={c.email}><ActionIcon size="sm" variant="subtle" component="a"
                        href={`mailto:${c.email}`} onClick={(e) => e.stopPropagation()}><IconMail size={14} /></ActionIcon></Tooltip>}
                    </Group>
                  </Table.Td>
                  <Table.Td><Text size="sm" c="dimmed">{(dateOf ? dateOf(c) : c.last_active) || "—"}</Text></Table.Td>
                  <Table.Td>
                    <Badge size="sm" variant={st.status ? "light" : "outline"} color={STATUS_COLOR[st.status]} tt="none">
                      {STATUS_LABEL[st.status] ?? st.status}{st.since ? ` · ${st.since.slice(5)}` : ""}
                    </Badge>
                  </Table.Td>
                </Table.Tr>
              );
            })}
          </Table.Tbody>
        </Table>
      </ScrollArea>
      {rows.length > 0 && (
        <Group justify="space-between" p="sm">
          <Text size="sm" c="dimmed">{(page - 1) * pp + 1}–{Math.min(page * pp, rows.length)} of {rows.length}</Text>
          <Group gap="xs">
            <Select size="xs" w={90} data={["25", "50", "100", "200"]} value={perPage} onChange={(v) => { setPerPage(v || "50"); setPage(1); }} allowDeselect={false} />
            <Pagination size="sm" total={pages} value={page} onChange={setPage} />
          </Group>
        </Group>
      )}
      {rows.length === 0 && <Text c="dimmed" ta="center" py="xl">No contacts match.</Text>}
    </Paper>
  );
}
