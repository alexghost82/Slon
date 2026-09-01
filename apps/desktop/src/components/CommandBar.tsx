import type { FormEvent } from "react";

interface CommandBarProps {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function CommandBar({ value, disabled, onChange, onSubmit }: CommandBarProps) {
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!disabled) onSubmit();
  };

  return (
    <form className="command-bar" onSubmit={submit} aria-label="Command input">
      <label htmlFor="command-input">Speak your command...</label>
      <div className="command-shell">
        <input
          id="command-input"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder=""
          autoComplete="off"
        />
        <button type="submit" disabled={disabled} aria-label="Send command">⌁</button>
      </div>
      <div className="suggested-actions" aria-label="Suggested actions">
        <button type="button"><span>◆</span> Voice assistant</button>
        <button type="button"><span>◈</span> Summarize chat</button>
        <button type="button"><span>◎</span> Open project</button>
        <button type="button"><span>⌕</span> Magic search</button>
      </div>
    </form>
  );
}