import { useMemo } from "react";
import { Button, Group, Paper, SimpleGrid, Stack, Text, Title } from "@mantine/core";
import { IconPlayerPlay } from "@tabler/icons-react";
import type { Ctx, Section } from "../App";
import { actedToday, isFollowUpDue, messagedToday, statusOf } from "../lib";
import ContactTable from "./ContactTable";

export default function TodayView({ mode, ctx, goTo }: { mode: "today" | "followups"; ctx: Ctx; goTo: (s: Section) => void }) {
  const { data } = ctx;
  const st = (id: string) => statusOf(data.status, id);

  const rows = useMemo(() => {
    if (mode === "followups") {
      return data.contacts.filter((c) => isFollowUpDue(st(c.id), data.today))
        .sort((a, b) => st(a.id).follow_up_on.localeCompare(st(b.id).follow_up_on));
    }
    // Still-queued first (the work left), then everything already handled today.
    return data.contacts.filter((c) => actedToday(st(c.id), data.today))
      .sort((a, b) => Number(st(b.id).status === "queued") - Number(st(a.id).status === "queued") || b.score - a.score);
  }, [data, mode]);

  const queued = rows.filter((c) => st(c.id).status === "queued");
  const messaged = data.contacts.filter((c) => messagedToday(st(c.id), data.today)).length;
  const target = Number(data.config.daily_target) || 30;
  const workList = mode === "today" ? queued : rows;

  return (
    <Stack gap="md">
      <Group justify="space-between" align="flex-end">
        <div>
          <Title order={3}>{mode === "today" ? "Today" : "Follow-ups due"}</Title>
          <Text size="sm" c="dimmed">{mode === "today"
            ? "Your queue for today. Work through it in the drawer: copy, send it yourself, then press m to log it and move on."
            : `People you contacted at least ${data.config.follow_up_days ?? 7} days ago who haven't replied yet.`}</Text>
        </div>
        <Button leftSection={<IconPlayerPlay size={16} />} disabled={!workList.length}
          onClick={() => ctx.open(workList[0].id, workList.map((c) => c.id))}>
          {mode === "today" ? `Start queue (${queued.length})` : `Work through (${rows.length})`}
        </Button>
      </Group>
      {mode === "today" && (
        <SimpleGrid cols={{ base: 1, sm: 3 }}>
          <Stat label="Messaged today" value={`${messaged} / ${target}`} />
          <Stat label="Still queued" value={String(queued.length)} />
          <Stat label="Follow-ups due" value={String(data.contacts.filter((c) => isFollowUpDue(st(c.id), data.today)).length)}
            action={() => goTo("followups")} />
        </SimpleGrid>
      )}
      {rows.length === 0 ? (
        <Paper withBorder p="xl" radius="md" ta="center">
          <Text c="dimmed">{mode === "today"
            ? "Nothing queued yet. Go to Creators, Journalists or Outlets, filter, and press “Build today's list”."
            : "No follow-ups due."}</Text>
          {mode === "today" && <Button mt="md" variant="light" onClick={() => goTo("creator")}>Go to Creators</Button>}
        </Paper>
      ) : (
        <ContactTable rows={rows} status={data.status} showKind onOpen={(id) => ctx.open(id, rows.map((c) => c.id))}
          dateLabel={mode === "followups" ? "Follow up on" : "Last active"}
          dateOf={mode === "followups" ? (c) => st(c.id).follow_up_on : undefined} />
      )}
    </Stack>
  );
}

function Stat({ label, value, action }: { label: string; value: string; action?: () => void }) {
  return (
    <Paper withBorder p="md" radius="md" onClick={action} style={action ? { cursor: "pointer" } : undefined}>
      <Text size="xs" c="dimmed" tt="uppercase" fw={700}>{label}</Text>
      <Text size="xl" fw={700}>{value}</Text>
    </Paper>
  );
}
