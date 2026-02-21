interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export function Toggle({
  checked,
  onChange,
  label,
  disabled = false,
}: ToggleProps) {
  return (
    <label className="inline-flex items-center gap-2.5 cursor-pointer select-none">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={[
          "relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors duration-200",
          "focus-visible:outline-none focus-visible:shadow-focus",
          "disabled:opacity-40 disabled:pointer-events-none",
          checked ? "bg-terra" : "bg-ink-faint",
        ].join(" ")}
      >
        <span
          className={[
            "pointer-events-none inline-block h-3.5 w-3.5 rounded-full bg-white shadow-subtle",
            "transition-transform duration-200 mt-[3px] ml-[3px]",
            checked ? "translate-x-[14px]" : "translate-x-0",
          ].join(" ")}
        />
      </button>
      {label && <span className="text-sm text-ink-secondary">{label}</span>}
    </label>
  );
}
