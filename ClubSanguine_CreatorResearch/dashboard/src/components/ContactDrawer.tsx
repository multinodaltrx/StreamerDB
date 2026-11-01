import { useEffect, useMemo, useState } from "react";
import {
  ActionIcon, Alert, Anchor, Badge, Button, CopyButton, Divider, Drawer, Group, Kbd, Paper, Select, Stack, Text,
  TextInput, Textarea, Timeline, Title, Tooltip,
} from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import {
  IconArrowLeft, IconArrowRight, IconCheck, IconCopy, IconExternalLink, IconMail, IconNote, IconPlayerSkipForward,
  IconStarFilled, IconArrowBackUp,
} from "@tabler/icons-react";
import type { Ctx } from "../App";
import ReachPanel from "./ReachPanel";
import type { Action, Contact } from "../types";
import {
  CHANNELS, STATUS_COLOR, STATUS_LABEL, TIER_COLOR, defaultChannel, fmtSubs, mailtoHref, renderMessage, statusOf,
  templateLabel, unfilled,
} from "../lib";

interface Props {
  ctx: Ctx;
  state: { id: string; queue: string[] } | null;
  onNavigate: (id: string) => void;
  onClose: () => void;
}

const OUTCOMES: [Action, string][] = [
  ["replied", "Replied"], ["interested", "Interested"], ["key_sent", "Key sent"],
  ["covered", "Covered"], ["declined", "Declined"], ["followed_up", "Followed up"],
];

export default function ContactDrawer({ ctx, state, onNavigate, onClose }: Props) {
  const { data } = ctx;
  const c: Contact | undefined = useMemo(() => data.contacts.find((x) => x.id === state?.id), [data.contacts, state?.id]);
  const idx = state && c ? state.queue.indexOf(c.id) : -1;
  const prevId = idx > 0 ? state!.queue[idx - 1] : null;
  const nextId = idx >= 0 && idx < (state?.queue.length ?? 0) - 1 ? state!.queue[idx + 1] : null;

  const [tplId, setTplId] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [channel, setChannel] = useState("email");
  const [note, setNote] = useState("");
  const [reveal, setReveal] = useState("");

  // New contact: pick the remembered template for its audience and a sensible channel.
  useEffect(() => {
    if (!c) return;
    setTplId(ctx.templateFor(c.kind)); setChannel(defaultChannel(c)); setNote(""); setReveal("");
  }, [c?.id]);
  // Re-render the editable message whenever the contact, template or config changes.
  useEffect(() => {
    if (!c || !tplId) return;
    const m = renderMessage(data.templates.find((t) => t.id === tplId), c, data.config);
    setSubject(m.subject); setBody(m.body);
  }, [c?.id, tplId, data.config]);

  const copy = (text: string) => navigator.clipboard.writeText(text);
  const record = async (action: Action, advance = false) => {
    if (!c) return;
    await ctx.log([{ contact_id: c.id, kind: c.kind, name: c.name, action, channel: ["contacted", "followed_up"].includes(action) ? channel : "",
      template: tplId, note }], `${c.name}: ${STATUS_LABEL[action] || action}`);
    setNote("");
    if (advance && nextId) onNavigate(nextId);
  };

  useHotkeys(state ? [
    ["j", () => nextId && onNavigate(nextId)],
    ["k", () => prevId && onNavigate(prevId)],
    ["ArrowRight", () => nextId && onNavigate(nextId)],
    ["ArrowLeft", () => prevId && onNavigate(prevId)],
    ["c", () => copy(body)],
    ["e", () => c?.email && copy(c.email)],
    ["m", () => record("contacted", true)],
    ["s", () => record("skip", true)],
  ] : []);

  if (!c) return <Drawer opened={false} onClose={onClose}>{null}</Drawer>;
  const st = statusOf(data.status, c.id);
  const missing = unfilled(subject + body);
  const about = c.links.find((l) => l[0] === "About (email)")?.[1];
  const outletMails = c.links.filter((l) => l[1].startsWith("mailto:"));

  return (
    <Drawer opened={!!state} onClose={onClose} position="right" size="xl" padding="lg"
      title={<Group gap="xs">
        <Badge color={TIER_COLOR[c.tier] || "gray"}>{c.tier || "–"}</Badge>
        <Title order={4}>{c.name}</Title>
        {c.hp && <IconStarFilled size={16} color="var(--mantine-color-yellow-6)" />}
      </Group>}>
      <Stack gap="md">
        <Group justify="space-between">
          <Group gap="xs">
            <Badge variant="light" color={STATUS_COLOR[st.status]}>{STATUS_LABEL[st.status] ?? st.status}{st.since && ` · ${st.since}`}</Badge>
            {st.follow_up_on && ["contacted", "followed_up"].includes(st.status) && <Badge variant="outline" color="orange">Follow up {st.follow_up_on}</Badge>}
          </Group>
          <Group gap={4}>
            <Text size="xs" c="dimmed">{idx + 1} / {state?.queue.length}</Text>
            <Tooltip label="Previous (k / ←)"><ActionIcon variant="default" disabled={!prevId} onClick={() => prevId && onNavigate(prevId)}><IconArrowLeft size={16} /></ActionIcon></Tooltip>
            <Tooltip label="Next (j / →)"><ActionIcon variant="default" disabled={!nextId} onClick={() => nextId && onNavigate(nextId)}><IconArrowRight size={16} /></ActionIcon></Tooltip>
          </Group>
        </Group>

        <Text size="sm" c="dimmed">
          {[c.id, `fit ${c.score}`, c.kind === "creator" ? `${fmtSubs(c.subs)} subscribers` : c.kind === "journalist" ? c.outlet : c.type,
            c.style, c.country, c.last_active && `active ${c.last_active}`, c.nextfest === "Yes" && "writes Next Fest roundups"].filter(Boolean).join(" · ")}
        </Text>
        {c.games.length > 0 && <Group gap={6}>{c.games.map((g) => <Badge key={g} variant="default" tt="none">{g}</Badge>)}</Group>}

        <ReachPanel c={c} subject={subject} body={body} />

        <Paper withBorder p="sm" radius="md">
          <Text size="xs" c="dimmed" fw={700} tt="uppercase" mb={6}>Contact route</Text>
          {c.email ? (
            <Group gap="xs">
              <Text fw={600} style={{ userSelect: "all" }}>{c.email}</Text>
              {c.email_revealed && <Badge size="xs" variant="light">revealed by you</Badge>}
              <CopyButton value={c.email}>{({ copied, copy }) =>
                <Button size="xs" variant="default" onClick={copy} leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />}>
                  {copied ? "Copied" : "Copy email"} <Kbd size="xs" ml={6}>e</Kbd></Button>}</CopyButton>
              <Button size="xs" component="a" target="_blank" rel="noopener" href={mailtoHref(c.email, subject, body)} leftSection={<IconMail size={14} />}>Open in mail app</Button>
            </Group>
          ) : c.route === "Gated email" ? (
            <Stack gap={6}>
              <Text size="sm">The business email is behind YouTube sign-in. Open the About panel, press <b>View email address</b>, then paste it here so it's saved for next time.</Text>
              <Group gap="xs">
                {about && <Button size="xs" component="a" href={about} target="_blank" rel="noopener" variant="light" rightSection={<IconExternalLink size={12} />}>Open About</Button>}
                <TextInput size="xs" placeholder="paste revealed email" value={reveal} onChange={(e) => setReveal(e.currentTarget.value)} w={240} />
                <Button size="xs" disabled={!reveal.includes("@")} onClick={() => ctx.reveal(c, reveal.trim())}>Save</Button>
              </Group>
            </Stack>
          ) : outletMails.length ? (
            <Stack gap={6}>
              <Text size="sm">No personal email published, so pitch through the outlet{outletMails.length > 1 ? "s" : ""}:</Text>
              {outletMails.map(([label, href]) => {
                const addr = href.slice("mailto:".length);
                return (
                  <Group gap="xs" key={href}>
                    <Text fw={600} style={{ userSelect: "all" }}>{addr}</Text>
                    <Text size="xs" c="dimmed">{label.replace(/ email$/, "")}</Text>
                    <CopyButton value={addr}>{({ copied, copy }) =>
                      <Button size="xs" variant="default" onClick={copy} leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />}>
                        {copied ? "Copied" : "Copy"}</Button>}</CopyButton>
                    <Button size="xs" component="a" target="_blank" rel="noopener" href={mailtoHref(addr, subject, body)} leftSection={<IconMail size={14} />}>Open in mail app</Button>
                  </Group>
                );
              })}
            </Stack>
          ) : (
            <Text size="sm">{c.links.some((l) => / submit$|^Submit$/.test(l[0]))
              ? "No email published. Use the submission form linked above."
              : c.route === "Unknown" ? "No public contact route recorded." : `${c.route}: use the links above.`}</Text>
          )}
        </Paper>

        <Paper withBorder p="sm" radius="md">
          <Group justify="space-between" mb={6}>
            <Text size="xs" c="dimmed" fw={700} tt="uppercase">Message</Text>
            <Select size="xs" w={200} allowDeselect={false} value={tplId}
              data={data.templates.map((t) => ({ value: t.id, label: templateLabel(t.id) }))}
              onChange={(v) => { if (v) { setTplId(v); ctx.setTemplateFor(c.kind, v); } }} />
          </Group>
          {missing.length > 0 && <Alert color="yellow" variant="light" p="xs" mb="xs">
            Unfilled: {missing.join(" ")}. Set them in <code>outreach/config.json</code> or edit them below.</Alert>}
          <Stack gap="xs">
            {subject !== "" && <TextInput label="Subject" value={subject} onChange={(e) => setSubject(e.currentTarget.value)}
              rightSection={<CopyButton value={subject}>{({ copied, copy }) =>
                <ActionIcon variant="subtle" onClick={copy}>{copied ? <IconCheck size={14} /> : <IconCopy size={14} />}</ActionIcon>}</CopyButton>} />}
            <Textarea value={body} onChange={(e) => setBody(e.currentTarget.value)} autosize minRows={6} maxRows={16} />
            <Group gap="xs">
              <CopyButton value={body}>{({ copied, copy }) =>
                <Button size="xs" onClick={copy} leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />}>
                  {copied ? "Copied" : "Copy message"} <Kbd size="xs" ml={6}>c</Kbd></Button>}</CopyButton>
              <Text size="xs" c="dimmed">Edits are for this message only. Change templates in <code>outreach/templates/</code>.</Text>
            </Group>
          </Stack>
        </Paper>

        <Paper withBorder p="sm" radius="md">
          <Text size="xs" c="dimmed" fw={700} tt="uppercase" mb={6}>Log what you did</Text>
          <Stack gap="xs">
            <Group gap="xs" align="flex-end">
              <Select size="xs" w={130} label="Channel" value={channel} onChange={(v) => setChannel(v || "email")} data={CHANNELS} allowDeselect={false} />
              <TextInput size="xs" style={{ flex: 1 }} label="Note (optional)" leftSection={<IconNote size={14} />} value={note} onChange={(e) => setNote(e.currentTarget.value)} />
            </Group>
            <Group gap="xs">
              <Button onClick={() => record("contacted", true)} leftSection={<IconCheck size={16} />}>
                Mark contacted{nextId ? " & next" : ""} <Kbd size="xs" ml={6}>m</Kbd></Button>
              <Button variant="default" onClick={() => record("skip", true)} leftSection={<IconPlayerSkipForward size={16} />}>
                Skip <Kbd size="xs" ml={6}>s</Kbd></Button>
              {note && <Button variant="subtle" onClick={() => record("note")}>Save note only</Button>}
              {st.status && <Button variant="subtle" color="gray" leftSection={<IconArrowBackUp size={16} />} onClick={() => record("undo")}>Undo last</Button>}
            </Group>
            <Group gap={6}>
              {OUTCOMES.map(([a, l]) => <Button key={a} size="xs" variant="light" color={STATUS_COLOR[a]} onClick={() => record(a)}>{l}</Button>)}
            </Group>
          </Stack>
        </Paper>

        {c.notes && <><Divider label="Research notes" labelPosition="left" /><Text size="sm" c="dimmed">{c.notes}</Text></>}

        {st.history.length > 0 && (
          <>
            <Divider label="History" labelPosition="left" />
            <Timeline active={st.history.length} bulletSize={14} lineWidth={2}>
              {[...st.history].reverse().map((h, i) => (
                <Timeline.Item key={i} title={<Text size="sm" fw={600}>{STATUS_LABEL[h.action] ?? h.action}{h.channel && ` via ${h.channel}`}</Text>}>
                  <Text size="xs" c="dimmed">{h.timestamp.replace("T", " ")}{h.template && ` · ${templateLabel(h.template)}`}</Text>
                  {h.note && <Text size="sm">{h.note}</Text>}
                </Timeline.Item>
              ))}
            </Timeline>
          </>
        )}
        <Text size="xs" c="dimmed">Shortcuts: <Kbd>j</Kbd>/<Kbd>k</Kbd> next/prev · <Kbd>c</Kbd> copy message · <Kbd>e</Kbd> copy email · <Kbd>m</Kbd> contacted &amp; next · <Kbd>s</Kbd> skip &amp; next</Text>
        <Anchor size="xs" c="dimmed" href="#" onClick={(e) => { e.preventDefault(); onClose(); }}>Close (Esc)</Anchor>
      </Stack>
    </Drawer>
  );
}
