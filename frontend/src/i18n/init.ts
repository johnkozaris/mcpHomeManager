import { createInstance } from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import ICU from "i18next-icu";
import resourcesToBackend from "i18next-resources-to-backend";
import { initReactI18next } from "react-i18next";
import {
  DEFAULT_LOCALE,
  DEFAULT_NAMESPACE,
  FALLBACK_LOCALE,
  LOCALE_COOKIE_NAME,
  LOCALE_STORAGE_KEY,
  SUPPORTED_LOCALES,
  TRANSLATION_NAMESPACES,
  resolveSupportedLocale,
} from "./config";

type LocaleNamespaceModule = {
  default: Record<string, unknown>;
};

const localeModules = import.meta.glob<LocaleNamespaceModule>("./locales/*/*.json");
const i18n = createInstance();

function getLocaleNamespaceCandidates(locale: string, namespace: string): string[] {
  const resolvedLocale = resolveSupportedLocale(locale);
  const fallbackPath = `./locales/${DEFAULT_LOCALE}/${namespace}.json`;

  if (resolvedLocale === DEFAULT_LOCALE) {
    return [fallbackPath];
  }

  return [`./locales/${resolvedLocale}/${namespace}.json`, fallbackPath];
}

async function loadNamespace(
  locale: string,
  namespace: string,
): Promise<Record<string, unknown>> {
  for (const candidatePath of getLocaleNamespaceCandidates(locale, namespace)) {
    const loader = localeModules[candidatePath];

    if (!loader) {
      continue;
    }

    const module = await loader();
    return module.default;
  }

  return {};
}

void i18n
  .use(LanguageDetector)
  .use(ICU)
  .use(
    resourcesToBackend((locale: string, namespace: string) =>
      loadNamespace(locale, namespace),
    ),
  )
  .use(initReactI18next)
  .init({
    supportedLngs: [...SUPPORTED_LOCALES],
    fallbackLng: FALLBACK_LOCALE,
    defaultNS: DEFAULT_NAMESPACE,
    fallbackNS: DEFAULT_NAMESPACE,
    ns: [...TRANSLATION_NAMESPACES],
    cleanCode: true,
    load: "currentOnly",
    nonExplicitSupportedLngs: true,
    returnNull: false,
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ["querystring", "localStorage", "cookie", "navigator", "htmlTag"],
      lookupQuerystring: "lang",
      lookupLocalStorage: LOCALE_STORAGE_KEY,
      lookupCookie: LOCALE_COOKIE_NAME,
      caches: ["localStorage", "cookie"],
      convertDetectedLanguage: (locale: string) => resolveSupportedLocale(locale),
    },
    react: {
      useSuspense: false,
      bindI18nStore: "added loaded",
    },
  });

export { i18n };
