export const SUPPORTED_LOCALES = [
  "en",
  "es",
  "pt-BR",
  "pt-PT",
  "zh-CN",
  "ja",
  "ko",
  "el",
  "de",
  "fr",
  "th",
  "it",
] as const;

export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

export const DEFAULT_LOCALE: SupportedLocale = "en";
export const FALLBACK_LOCALE: SupportedLocale = DEFAULT_LOCALE;

export const DEFAULT_NAMESPACE = "common";
export const TRANSLATION_NAMESPACES = [
  DEFAULT_NAMESPACE,
  "components",
  "nav",
  "serviceMeta",
  "tokenGuides",
  "errors",
  "backendErrors",
  "time",
  "auth",
  "dashboard",
  "services",
  "serviceDetail",
  "tools",
  "agents",
  "logs",
  "users",
  "settings",
  "notFound",
] as const;

export const LOCALE_STORAGE_KEY = "mcp_home_locale";
export const LOCALE_COOKIE_NAME = "mcp_home_locale";

const LOCALE_ALIASES: Readonly<Record<string, SupportedLocale>> = {
  en: "en",
  es: "es",
  pt: "pt-PT",
  "pt-br": "pt-BR",
  "pt-pt": "pt-PT",
  zh: "zh-CN",
  "zh-cn": "zh-CN",
  ja: "ja",
  ko: "ko",
  el: "el",
  de: "de",
  fr: "fr",
  th: "th",
  it: "it",
};

/** Native display names for each locale — shown in the language picker. */
export const LOCALE_DISPLAY_NAMES: Readonly<Record<SupportedLocale, string>> = {
  en: "English",
  es: "Español",
  "pt-BR": "Português (Brasil)",
  "pt-PT": "Português (Portugal)",
  "zh-CN": "简体中文",
  ja: "日本語",
  ko: "한국어",
  el: "Ελληνικά",
  de: "Deutsch",
  fr: "Français",
  th: "ภาษาไทย",
  it: "Italiano",
};

export function resolveSupportedLocale(locale: string | null | undefined): SupportedLocale {
  if (!locale) {
    return DEFAULT_LOCALE;
  }

  const normalized = locale.trim().toLowerCase().replaceAll("_", "-");

  return (
    LOCALE_ALIASES[normalized] ??
    LOCALE_ALIASES[normalized.split("-")[0] ?? ""] ??
    DEFAULT_LOCALE
  );
}
