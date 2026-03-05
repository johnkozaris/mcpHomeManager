import "@testing-library/jest-dom";
import { TRANSLATION_NAMESPACES } from "@/i18n/config";
import { i18n } from "@/i18n/init";

async function waitForI18nInitialization() {
  if (i18n.isInitialized) {
    return;
  }

  await new Promise<void>((resolve) => {
    const handleInitialized = () => {
      i18n.off("initialized", handleInitialized);
      resolve();
    };
    i18n.on("initialized", handleInitialized);
  });
}

beforeAll(async () => {
  await waitForI18nInitialization();
  await i18n.changeLanguage("en");
  await i18n.loadNamespaces([...TRANSLATION_NAMESPACES]);
});

beforeEach(async () => {
  if (i18n.language !== "en") {
    await i18n.changeLanguage("en");
  }
});
