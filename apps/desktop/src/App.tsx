import { useEffect, useState } from "react";
import { AssistantOrb } from "./components/AssistantOrb";
import { CommandBar } from "./components/CommandBar";
import { LeftRail } from "./components/LeftRail";
import { RightRail } from "./components/RightRail";
import { SettingsDrawer } from "./components/SettingsDrawer";
import { readBackendSnapshot } from "./lib/backendClient";
import type { AssistantState, BackendSnapshot } from "./lib/types";

const initialBackend: BackendSnapshot = {
  state: "starting",
  health: null,
  status: null,
  message: "Waiting for local backend...",
  checkedAt: new Date().toISOString(),
};

function assistantStateForBackend(snapshot: BackendSnapshot): AssistantState {
  if (snapshot.state === "offline") return "offline";
  if (snapshot.state === "unauthorized") return "missingApiKey";
  if (snapshot.state === "error") return "error";
  return "idle";
}

export default function App() {
  const [backend, setBackend] = useState<BackendSnapshot>(initialBackend);
  const [assistantState, setAssistantState] = useState<AssistantState>("idle");
  const [command, setCommand] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const refresh = async () => {
      const snapshot = await readBackendSnapshot();
      if (cancelled) return;
      setBackend(snapshot);
      setAssistantState((current) => (current === "thinking" ? current : assistantStateForBackend(snapshot)));
    };

    void refresh();
    const interval = window.setInterval(refresh, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const submitCommand = () => {
    if (command.trim().length === 0) return;
    setAssistantState("thinking");
    setCommand("");
    window.setTimeout(() => setAssistantState(assistantStateForBackend(backend)), 1600);
  };

  return (
    <main className="app-shell">
      <div className="cosmic-field" aria-hidden="true" />
      <div className="scanline" aria-hidden="true" />
      <LeftRail assistantState={assistantState} backend={backend} />
      <section className="stage" aria-label="Slon assistant console">
        <header className="topline">
          <span>slon is always near</span>
          <span>{new Date(backend.checkedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
        </header>
        <AssistantOrb state={assistantState} />
        <CommandBar
          value={command}
          disabled={command.trim().length === 0}
          onChange={setCommand}
          onSubmit={submitCommand}
        />
        <button className="settings-fab" type="button" onClick={() => setSettingsOpen(true)} aria-label="Open settings">
          +
        </button>
      </section>
      <RightRail backend={backend} />
      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </main>
  );
}