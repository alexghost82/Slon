import type { ActivityItem, BackendSnapshot } from "../lib/types";

interface RightRailProps {
  backend: BackendSnapshot;
}

const activity: ActivityItem[] = [
  { label: "Voice core", value: "42%", tone: "primary" },
  { label: "Memory", value: "98%", tone: "violet" },
  { label: "Tasks", value: "4", tone: "success" },
  { label: "Latency", value: "local", tone: "muted" },
];

export function RightRail({ backend }: RightRailProps) {
  return (
    <aside className="rail rail-right" aria-label="Assistant telemetry">
      <section className="hud-block activity-card">
        <p className="section-kicker">ai activity</p>
        <div className="bar-chart" aria-hidden="true">
          {Array.from({ length: 18 }, (_, index) => (
            <span key={index} style={{ height: `${22 + ((index * 17) % 58)}%` }} />
          ))}
        </div>
      </section>

      <section className="hud-block metric-stack">
        <p className="section-kicker">memory core</p>
        <strong>42%</strong>
        <div className="thin-meter"><span /></div>
      </section>

      <section className="hud-block data-list">
        <p className="section-kicker">active tasks</p>
        {activity.map((item) => (
          <div key={item.label} className={`data-row ${item.tone ?? "muted"}`}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </section>

      <section className="hud-block recent-list">
        <p className="section-kicker">recent commands</p>
        <p>Waiting for command stream</p>
        <p>{backend.message}</p>
      </section>

      <section className="hud-block environment-card">
        <p className="section-kicker">environment</p>
        <strong>22°</strong>
        <span>{backend.health ? `${backend.health.bind_host}:${backend.health.bind_port}` : "backend offline"}</span>
      </section>
    </aside>
  );
}