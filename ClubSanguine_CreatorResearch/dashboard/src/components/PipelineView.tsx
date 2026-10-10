import { useMemo, useState } from "react";
import { Badge, Paper, ScrollArea, SegmentedControl, Stack, Table, Text, Title } from "@mantine/core";
import type { Ctx } from "../App";
import { STATUS_COLOR, STATUS_LABEL, sortContacts, statusOf } from "../lib";
import ContactTable from "./ContactTable";

const KINDS = [["creator", "Creators"], ["journalist", "Journalists"], ["outlet", "Outlets"]] as const;
const STATUSES = Object.keys(STATUS_LABEL).filter(Boolean);

export default function PipelineView({ ctx }: { ctx: Ctx }) {
  const { data } = ctx;
  const [kind, setKind] = useState("all");
  const touched = useMemo(() => sortContacts(
    data.contacts.filter((c) => statusOf(data.status, c.id).status && (kind === "all" || c.kind === kind)),
    "status", "desc", data.status), [data, kind]);
  const n = (k: string, s: string) => data.contacts.filter((c) => c.kind === k && statusOf(data.status, c.id).status === s).length;

  return (
    <Stack gap="md">
      <div>
        <Title order={3}>Pipeline</Title>
        <Text size="sm" c="dimmed">Everyone you've touched, by current status. The full history is in <code>outreach/outreach_log.csv</code>.</Text>
      </div>
      <Paper withBorder radius="md">
        <ScrollArea>
          <Table miw={760} ta="center">
            <Table.Thead>
              <Table.Tr><Table.Th />{STATUSES.map((s) => <Table.Th key={s} ta="center">
                <Badge variant="light" color={STATUS_COLOR[s]} tt="none">{STATUS_LABEL[s]}</Badge></Table.Th>)}</Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {KINDS.map(([k, label]) => (
                <Table.Tr key={k}><Table.Th>{label}</Table.Th>
                  {STATUSES.map((s) => <Table.Td key={s}>{n(k, s) || <Text span c="dimmed">·</Text>}</Table.Td>)}</Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </ScrollArea>
      </Paper>
      <SegmentedControl value={kind} onChange={setKind} w="fit-content"
        data={[{ value: "all", label: "All" }, ...KINDS.map(([value, label]) => ({ value, label }))]} />
      <ContactTable rows={touched} status={data.status} showKind onOpen={(id) => ctx.open(id, touched.map((c) => c.id))} />
    </Stack>
  );
}
