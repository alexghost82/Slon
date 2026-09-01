interface SettingsDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsDrawer({ open, onClose }: SettingsDrawerProps) {
  return (
    <div className={`drawer-layer ${open ? "open" : ""}`} aria-hidden={!open}>
      <button className="drawer-scrim" type="button" onClick={onClose} tabIndex={open ? 0 : -1} aria-label="Close settings" />
      <aside className="settings-drawer" aria-label="Settings" aria-modal="true">
        <div className="drawer-header">
          <div>
            <p className="eyebrow">Configuration</p>
            <h2>Provider settings</h2>
          </div>
          <button type="button" onClick={onClose}>Close</button>
        </div>
        <label>
          Provider
          <select defaultValue="gemini">
            <option value="gemini">Gemini</option>
            <option value="openai">OpenAI</option>
            <option value="openrouter">OpenRouter</option>
            <option value="local">Local</option>
          </select>
        </label>
        <label>
          Model
          <input defaultValue="auto" />
        </label>
        <label>
          API key
          <input type="password" placeholder="Stored by Python backend" />
        </label>
        <p className="drawer-note">Secrets are backend-owned. This scaffold does not persist raw keys in frontend storage.</p>
      </aside>
    </div>
  );
}