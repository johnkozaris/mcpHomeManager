import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import tanstackQuery from "@tanstack/eslint-plugin-query";
import oxlint from "eslint-plugin-oxlint";

export default tseslint.config(
  js.configs.recommended,
  tseslint.configs.recommended,
  reactHooks.configs.flat["recommended-latest"],
  ...tanstackQuery.configs["flat/recommended"],
  {
    ignores: ["dist/"],
  },
  // Must be last — auto-disables ESLint rules already covered by oxlint
  ...oxlint.buildFromOxlintConfigFile("./.oxlintrc.json"),
);
