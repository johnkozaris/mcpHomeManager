import { lazy, Suspense, useState } from "react";
import { useTheme } from "@/hooks/useTheme";
import { useTranslation } from "react-i18next";

const Editor = lazy(() =>
  import("@monaco-editor/react")
    .then((m) => ({ default: m.default }))
    .catch(() => ({ default: null as never })),
);

interface Props {
  value: string;
  onChange?: (value: string) => void;
  language?: string;
  height?: string;
  readOnly?: boolean;
}

function FallbackTextarea({ value, onChange, height, readOnly }: Props) {
  return (
    <div className="rounded-xl overflow-hidden border border-line">
      <textarea
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        readOnly={readOnly}
        className="w-full bg-canvas-tertiary text-ink font-mono text-sm p-3 resize-y focus:outline-none"
        style={{ height, minHeight: "100px" }}
        spellCheck={false}
      />
    </div>
  );
}

export function MonacoEditor({
  value,
  onChange,
  language = "json",
  height = "300px",
  readOnly = false,
}: Props) {
  const { t } = useTranslation("components", { keyPrefix: "ui.monacoEditor" });
  const { theme } = useTheme();
  const [errors, setErrors] = useState<string[]>([]);
  const [loadFailed, setLoadFailed] = useState(false);

  function handleValidation(markers: { message: string; severity: number }[]) {
    setErrors(markers.filter((m) => m.severity >= 8).map((m) => m.message));
  }

  if (loadFailed) {
    return (
      <FallbackTextarea
        value={value}
        onChange={onChange}
        height={height}
        readOnly={readOnly}
      />
    );
  }

  return (
    <Suspense
      fallback={
        <div
          className="flex items-center justify-center rounded-xl border border-line bg-canvas-tertiary text-sm text-ink-tertiary"
          style={{ height }}
        >
          {t("loading")}
        </div>
      }
    >
      <MonacoInner
        value={value}
        onChange={onChange}
        language={language}
        height={height}
        readOnly={readOnly}
        theme={theme}
        onValidate={handleValidation}
        onLoadError={() => setLoadFailed(true)}
        errors={errors}
      />
    </Suspense>
  );
}

function MonacoInner({
  value,
  onChange,
  language,
  height,
  readOnly,
  theme,
  onValidate,
  errors,
}: Props & {
  theme: string;
  onValidate: (markers: { message: string; severity: number }[]) => void;
  onLoadError: () => void;
  errors: string[];
}) {
  return (
    <div className="space-y-1">
      <div className="rounded-xl overflow-hidden border border-line">
        <Editor
          height={height}
          language={language}
          value={value}
          onChange={(v) => onChange?.(v ?? "")}
          onValidate={onValidate}
          theme={theme === "dark" ? "vs-dark" : "light"}
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            padding: { top: 12 },
          }}
        />
      </div>
      {errors.length > 0 && <p className="text-xs text-rust">{errors[0]}</p>}
    </div>
  );
}
