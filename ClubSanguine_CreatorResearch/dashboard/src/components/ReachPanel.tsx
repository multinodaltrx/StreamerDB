import { Button, Group, Paper, Stack, Text, Tooltip } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  IconBrandBluesky, IconBrandDiscord, IconBrandFacebook, IconBrandInstagram, IconBrandKick, IconBrandLinkedin,
  IconBrandMastodon, IconBrandPatreon, IconBrandReddit, IconBrandThreads, IconBrandTiktok, IconBrandTwitch,
  IconBrandX, IconBrandYoutube, IconExternalLink, IconFileText, IconForms, IconLink, IconMail, IconSend, IconWorld,
} from "@tabler/icons-react";
import type { Contact } from "../types";
import { mailtoHref } from "../lib";

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

/** The big "Message them" button plus every public social / contact link, grouped. */
export default function ReachPanel({ c, subject, body }: { c: Contact; subject: string; body: string }) {
  const route = c.message;
  const go = async () => {
    if (!route.url) return;
    if (route.how === "email") {
      window.open(mailtoHref(route.url.slice(7), subject, body), "_blank", "noopener");
      return;
    }
    // For DMs, Discord and forms: put the message on the clipboard first, then open the page.
    try { await navigator.clipboard.writeText(body); } catch { /* clipboard blocked; still open */ }
    notifications.show({ message: "Message copied: paste it once the page opens", color: "teal", autoClose: 2500 });
    window.open(route.url, "_blank", "noopener");
  };
  const reach = c.links.filter(([l]) => !["YouTube", "About (email)", "Next Fest piece", "Site", "Author page"].includes(l));
  const info = c.links.filter(([l]) => ["YouTube", "About (email)", "Next Fest piece", "Site", "Author page"].includes(l));

  return (
    <Paper withBorder p="sm" radius="md">
      <Stack gap="xs">
        <Group justify="space-between" wrap="nowrap">
          <Text size="xs" c="dimmed" fw={700} tt="uppercase">Reach them</Text>
          <Text size="xs" c="dimmed">best route first</Text>
        </Group>
        <Button size="md" fullWidth leftSection={<IconSend size={18} />} disabled={!route.url} onClick={go}
          rightSection={route.how !== "email" && route.url ? <IconExternalLink size={14} /> : null}>
          Message them: {route.label}
        </Button>
        {reach.length > 0 && (
          <Group gap={6}>
            {reach.map(([label, url]) => {
              const Icon = iconFor(url, label);
              const isMail = url.startsWith("mailto:");
              return (
                <Tooltip key={url} label={isMail ? url.slice(7) : url} withinPortal>
                  <Button component="a" size="xs" variant="light" leftSection={<Icon size={14} />}
                    href={isMail ? mailtoHref(url.slice(7), subject, body) : url} target={isMail ? undefined : "_blank"} rel="noopener">
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
