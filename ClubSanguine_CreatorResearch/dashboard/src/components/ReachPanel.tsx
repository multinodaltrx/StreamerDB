import { Button, Group, Paper, SegmentedControl, Select, Stack, Text, Tooltip } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  IconBrandBluesky, IconBrandDiscord, IconBrandFacebook, IconBrandInstagram, IconBrandKick, IconBrandLinkedin,
  IconBrandMastodon, IconBrandPatreon, IconBrandReddit, IconBrandThreads, IconBrandTiktok, IconBrandTwitch,
  IconBrandX, IconBrandYoutube, IconExternalLink, IconFileText, IconForms, IconLink, IconMail, IconSend, IconWorld,
} from "@tabler/icons-react";
import type { Contact, How } from "../types";
import { showPressKit, showTrailer } from "../api";
import { HOW_LABEL, isYoutube, mailtoHref, openLink, openMail } from "../lib";

const ICONS: [RegExp, typeof IconLink][] = [
  [/discord/i, IconBrandDiscord], [/bsky\.app/i, IconBrandBluesky], [/(x|twitter)\.com/i, IconBrandX],
  [/instagram/i, IconBrandInstagram], [/tiktok/i, IconBrandTiktok], [/threads\.net/i, IconBrandThreads],
  [/twitch\.tv/i, IconBrandTwitch], [/kick\.com/i, IconBrandKick], [/youtube\.com|youtu\.be/i, IconBrandYoutube],
  [/facebook/i, IconBrandFacebook], [/linkedin/i, IconBrandLinkedin], [/mastodon|mstdn|\.social\//i, IconBrandMastodon],
  [/reddit/i, IconBrandReddit], [/patreon/i, IconBrandPatreon], [/^mailto:/i, IconMail],
];

export function iconFor(url: string, label = "") {
  if (/submit|contact/i.test(label)) return IconForms;
  for (const [re, Icon] of ICONS) if (re.test(url)) return Icon;
  return label === "Site" || label === "Author page" ? IconWorld : IconLink;
}

interface Props {
  c: Contact;
  subject: string;
  body: string;
  /** Channel being used; switching it also switches the template in the drawer. */
  via: How;
  onVia: (how: How) => void;
  /** They declined: no Message button. */
  blocked?: boolean;
  /** Gmail account the email goes out from, and the accounts to choose between. */
  sender: string;
  senders: string[];
  onSender: (s: string) => void;
}

/** The big "Message them" button for the chosen channel, plus every public social / contact link, grouped. */
export default function ReachPanel({ c, subject, body, via, onVia, blocked, sender, senders, onSender }: Props) {
  const route = c.reach.find((r) => r.how === via) || c.reach[0];
  const hasMail = c.links.some(([, url]) => url.startsWith("mailto:")) || route.how === "email";
  const go = async () => {
    if (!route.url) return;
    if (route.how === "email") {
      openMail(route.url.slice(7), subject, body, sender);
      return;
    }
    // For DMs, Discord and forms: put the message on the clipboard first, then open the page.
    try { await navigator.clipboard.writeText(body); } catch { /* clipboard blocked; still open */ }
    notifications.show({ message: "Message copied: paste it once the page opens", color: "teal", autoClose: 2500 });
    openLink(route.url);
  };
  const reach = c.links.filter(([l]) => !["YouTube", "About (email)", "Next Fest piece", "Site", "Author page"].includes(l));
  const info = c.links.filter(([l]) => ["YouTube", "About (email)", "Next Fest piece", "Site", "Author page"].includes(l));

  return (
    <Paper withBorder p="sm" radius="md">
      <Stack gap="xs">
        <Group justify="space-between" wrap="nowrap">
          <Text size="xs" c="dimmed" fw={700} tt="uppercase">Reach them</Text>
          <Text size="xs" c="dimmed">{c.reach.length > 1 ? "pick a channel" : "only route on record"}</Text>
        </Group>
        {c.reach.length > 1 && (
          <SegmentedControl fullWidth size="xs" value={route.how} onChange={(v) => onVia(v as How)}
            data={c.reach.map((r) => ({ value: r.how, label: HOW_LABEL[r.how] }))} />
        )}
        <Button size="md" fullWidth leftSection={<IconSend size={18} />} disabled={!route.url || blocked} onClick={go}
          rightSection={route.how !== "email" && route.url ? <IconExternalLink size={14} /> : null}>
          Message them: {route.label}
        </Button>
        {(route.how === "discord" || route.how === "dm") && (
          <Text size="xs" c="dimmed" ta="center">First message has no links. Send the Steam demo link only after they say yes.
            {route.how === "discord" && " Use the server's game-suggestion channel if it has one, and follow its rules."}</Text>
        )}
        {route.how === "web" && (
          <Text size="xs" c="orange" ta="center">No direct contact on record. This only opens their site.</Text>
        )}
        {hasMail && (senders.length > 1 ? (
          <Group gap="xs" justify="center" wrap="nowrap">
            <Text size="xs" c="dimmed">Send from</Text>
            <Select size="xs" w={240} allowDeselect={false} value={sender} data={senders} onChange={(v) => v && onSender(v)} />
            <Text size="xs" c="dimmed">(opens in its Chrome profile)</Text>
          </Group>
        ) : (
          <Text size="xs" c="dimmed" ta="center">
            Sends from <b>{sender || "your default mail app"}</b>{sender ? " (opens in its Chrome profile)" : ""}
          </Text>
        ))}
        {c.kind !== "creator" && (
          <Button size="xs" variant="default" leftSection={<IconFileText size={14} />}
            onClick={() => showPressKit().then(() => notifications.show({ message: "Press kit PDF selected in Explorer: drag it into the compose window", color: "teal", autoClose: 3500 }))
              .catch(() => notifications.show({ message: "Press kit file not found (config press_kit_file)", color: "red" }))}>
            Show press kit PDF to attach
          </Button>
        )}
        {c.kind !== "creator" && (
          <Button size="xs" variant="default" leftSection={<IconFileText size={14} />}
            onClick={() => showTrailer().then(() => notifications.show({ message: "Trailer MP4 selected in Explorer", color: "teal", autoClose: 3000 }))
              .catch(() => notifications.show({ message: "Trailer file not found (config trailer_file)", color: "red" }))}>
            Show trailer MP4
          </Button>
        )}
        {reach.length > 0 && (
          <Group gap={6}>
            {reach.map(([label, url]) => {
              const Icon = iconFor(url, label);
              const isMail = url.startsWith("mailto:");
              return (
                <Tooltip key={url} label={isMail ? url.slice(7) : url} withinPortal>
                  <Button component="a" size="xs" variant="light" leftSection={<Icon size={14} />}
                    href={isMail ? mailtoHref(url.slice(7), subject, body, sender) : url} target={isMail ? undefined : "_blank"} rel="noopener"
                    onClick={isMail ? (e) => { e.preventDefault(); openMail(url.slice(7), subject, body, sender); } : isYoutube(url) ? (e) => { e.preventDefault(); openLink(url); } : undefined}>
                    {label}
                  </Button>
                </Tooltip>
              );
            })}
          </Group>
        )}
        <Group gap={6}>
          {info.map(([label, url]) => {
            const Icon = iconFor(url, label);
            return <Button key={url} component="a" href={url} target="_blank" rel="noopener" size="xs" variant="subtle"
              onClick={isYoutube(url) ? (e: React.MouseEvent) => { e.preventDefault(); openLink(url); } : undefined}
              leftSection={<Icon size={14} />}>{label}</Button>;
          })}
          {c.evidence.map((url, i) => (
            <Button key={url} component="a" href={url} target="_blank" rel="noopener" size="xs" variant="subtle"
              leftSection={<IconFileText size={14} />}>Evidence {i + 1}</Button>
          ))}
        </Group>
      </Stack>
    </Paper>
  );
}
