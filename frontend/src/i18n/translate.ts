import { i18n } from "./init";

type TranslateOptions = Record<string, unknown>;

export function translateText(
  key: string,
  fallback: string,
  options?: TranslateOptions,
): string {
  const translated = i18n.t(key, { ...options, defaultValue: fallback });
  return translated === key ? fallback : translated;
}

export function translateList(
  key: string,
  fallback: string[],
  options?: TranslateOptions,
): string[] {
  const translated = i18n.t(key, { ...options, returnObjects: true });
  if (!Array.isArray(translated)) {
    return fallback;
  }

  const normalized = translated.filter(
    (item): item is string => typeof item === "string",
  );
  return normalized.length > 0 ? normalized : fallback;
}
