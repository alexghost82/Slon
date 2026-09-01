import type { AssistantState, BackendSnapshot } from "../lib/types";

interface LeftRailProps {
  assistantState: AssistantState;
  backend: BackendSnapshot;
}

export function LeftRail({ assistantState, backend }: LeftRailProps) {
  return (
    <aside className="rail rail-left" aria-label="Assistant status">
      <section className="hud-block brand-block">
        <h1>SLON</h1>
        <span>voice assistant</span>
      </section>

      <section className="hud-block">
        <p className="section-kicker">status</p>
        <div className={`status-line ${backend.state}`}><span />{backend.state}</div>
      </section>

      <section className="hud-block">
        <p className="section-kicker">listening</p>
        <div className="mini-wave" aria-hidden="true">
          {Array.from({ length: 24 }, (_, index) => (
            <span key={index} style={{ animationDelay: `${index * 42}ms` }} />
          ))}
        </div>
        <p className="microcopy">{assistantState === "listening" ? "mic stream armed" : "wake channel standby"}</p>
      </section>

      <section className="hud-block voice-panel">
        <p className="section-kicker">voice input</p>
        <strong>{assistantState}</strong>
      </section>

      <section className="hud-block connections">
        <p className="section-kicker">connections</p>
        <div><span />Backend <strong>{backend.health ? "online" : "offline"}</strong></div>
        <div><span />Control API <strong>{backend.state === "unauthorized" ? "locked" : backend.state}</strong></div>
        <div><span />Desktop <strong>local</strong></div>
      </section>

      <section className="hud-block shortcut-list">
        <p className="section-kicker">shortcuts</p>
        <button type="button">Cmd K</button>
        <button type="button">Mute</button>
        <button type="button">History</button>
        <button type="button">Settings</button>
      </section>
    </aside>
  );
}