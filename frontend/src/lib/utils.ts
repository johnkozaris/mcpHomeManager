/**
 * Shared utilities — formatting, localStorage helpers, and common patterns.
 *
 * Keep this module free of React imports so it can be used anywhere.
 */

/* ─── Time formatting ──────────────────────────────────────── */

/** Human-friendly relative time string ("just now", "5m ago", "2d ago"). */
export function formatRelativeTime(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/* ─── localStorage helpers (dismissible banners) ───────────── */

const DISMISS_PREFIX = "dismiss_";

export function isDismissed(key: string): boolean {
  return localStorage.getItem(`${DISMISS_PREFIX}${key}`) === "1";
}

export function dismiss(key: string): void {
  localStorage.setItem(`${DISMISS_PREFIX}${key}`, "1");
}

/* ─── MCP endpoint ─────────────────────────────────────────── */

/** Build the public MCP endpoint URL from the current origin. */
export function getMcpEndpoint(): string {
  return `${window.location.origin}/mcp/`;
}

/* ─── MCP JSON config ─────────────────────────────────────── */

/** Build the standard MCP JSON config snippet for agent setup guides. */
export function buildMcpJsonConfig(
  mcpEndpoint: string,
  apiKey?: string | null,
): string {
  return JSON.stringify(
    {
      mcpServers: {
        homelab: {
          url: mcpEndpoint,
          headers: {
            Authorization: `Bearer ${apiKey ?? "YOUR_API_KEY"}`,
          },
        },
      },
    },
    null,
    2,
  );
}

/* ─── API error parsing ────────────────────────────────────── */

/** Extract a human-readable message from an API error response.
 *  Handles both `{detail: "..."}` and `{extra: [{message: "..."}]}` shapes. */
export function parseApiError(
  error: unknown,
  fallback = "Something went wrong",
): string {
  const msg = error instanceof Error ? error.message : "";
  const body = msg.replace(/^\d+:\s*/, "");
  try {
    const parsed = JSON.parse(body);
    if (parsed.extra?.[0]?.message) return parsed.extra[0].message as string;
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // Not JSON — return the raw message
  }
  return body || fallback;
}
