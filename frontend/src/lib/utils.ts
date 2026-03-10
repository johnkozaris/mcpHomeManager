/** Formatting, localStorage helpers, and MCP config builders. No React imports. */
import { translateText } from "@/i18n/translate";

interface BackendMessagePayload {
  message?: unknown;
  detail?: unknown;
  code?: unknown;
  message_code?: unknown;
  extra?: unknown;
}

interface ResolveBackendMessageOptions {
  fallback?: string;
  includeRawDetail?: boolean;
  preferExtraMessage?: boolean;
}

const TRANSLATION_MISS_SENTINEL = "__backend_error_translation_missing__";
const DETAIL_SEPARATOR = " — ";

/** Human-friendly relative time string ("just now", "5m ago", "2d ago"). */
export function formatRelativeTime(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return translateText("time:relative.justNow", "just now");
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return translateText("time:relative.minutesAgo", "{count}m ago", {
      count: minutes,
    });
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return translateText("time:relative.hoursAgo", "{count}h ago", {
      count: hours,
    });
  }
  return translateText("time:relative.daysAgo", "{count}d ago", {
    count: Math.floor(hours / 24),
  });
}

const DISMISS_PREFIX = "dismiss_";

export function isDismissed(key: string): boolean {
  return localStorage.getItem(`${DISMISS_PREFIX}${key}`) === "1";
}

export function dismiss(key: string): void {
  localStorage.setItem(`${DISMISS_PREFIX}${key}`, "1");
}

/** Build the public MCP endpoint URL from the current origin. */
export function getMcpEndpoint(): string {
  return `${window.location.origin}/mcp/`;
}

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
            Authorization: `Bearer ${apiKey ?? translateText("common:mcp.placeholders.apiKey", "YOUR_API_KEY")}`,
          },
        },
      },
    },
    null,
    2,
  );
}

/** Extract a human-readable message from an API error response.
 *  Handles both `{detail: "..."}` and `{extra: [{message: "..."}]}` shapes. */
export function parseApiError(
  error: unknown,
  fallback = translateText("errors:api.generic", "Something went wrong"),
): string {
  const msg = error instanceof Error ? error.message : "";
  const body = msg.replace(/^\d+:\s*/, "");
  try {
    const parsed = JSON.parse(body);
    if (typeof parsed === "string") return parsed;
    if (parsed && typeof parsed === "object") {
      return resolveBackendMessage(parsed as BackendMessagePayload, {
        fallback,
        includeRawDetail: true,
        preferExtraMessage: true,
      });
    }
  } catch {
    // Not JSON — return the raw message
  }
  return body || fallback;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  return value as Record<string, unknown>;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function getExtraPayload(extra: unknown): Record<string, unknown> | null {
  if (Array.isArray(extra)) {
    return asRecord(extra[0]);
  }
  return asRecord(extra);
}

function getExtraMessage(extra: unknown): string | null {
  const payload = getExtraPayload(extra);
  return asString(payload?.message);
}

function getExtraCode(extra: unknown): string | null {
  const payload = getExtraPayload(extra);
  return asString(payload?.message_code) ?? asString(payload?.code);
}

function getBackendMessageCode(
  payload: BackendMessagePayload | null | undefined,
): string | null {
  if (!payload) return null;
  return (
    asString(payload.message_code) ??
    asString(payload.code) ??
    getExtraCode(payload.extra)
  );
}

function getBackendRawMessage(
  payload: BackendMessagePayload,
  preferExtraMessage = false,
): string | null {
  const extraMessage = getExtraMessage(payload.extra);
  const detail = asString(payload.detail);
  const message = asString(payload.message);

  if (preferExtraMessage) {
    return extraMessage ?? detail ?? message;
  }
  return message ?? detail ?? extraMessage;
}

function translateBackendMessageCode(code: string): string | null {
  const translated = translateText(
    `backendErrors:${code}`,
    TRANSLATION_MISS_SENTINEL,
    { keySeparator: false },
  );
  return translated === TRANSLATION_MISS_SENTINEL ? null : translated;
}

export function resolveBackendMessage(
  payload: BackendMessagePayload | null | undefined,
  options: ResolveBackendMessageOptions = {},
): string {
  const fallback =
    options.fallback ??
    translateText("errors:api.generic", "Something went wrong");
  if (!payload) return fallback;

  const raw = getBackendRawMessage(payload, options.preferExtraMessage);
  const messageCode = getBackendMessageCode(payload);
  if (!messageCode) return raw ?? fallback;

  const localized = translateBackendMessageCode(messageCode);
  if (!localized) return raw ?? fallback;

  if (options.includeRawDetail && raw && raw !== localized) {
    return `${localized}${DETAIL_SEPARATOR}${raw}`;
  }
  return localized;
}
