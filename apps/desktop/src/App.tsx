import { useEffect, useMemo, useState } from "react";
import { EnergyCanvas } from "./components/EnergyCanvas";
import { SettingsDrawer } from "./components/SettingsDrawer";
import { readBackendSnapshot } from "./lib/backendClient";
import type { BackendSnapshot } from "./lib/types";

type LogTone = "" | "warn" | "muted";

interface LogLine {
  time: string;
  text: string;
  tone: LogTone;
}

const initialBackend: BackendSnapshot = {
  state: "starting",
  health: null,
  status: null,
  message: "Waiting for local backend...",
  checkedAt: new Date().toISOString(),
};

const initialLogs: LogLine[] = [
  { time: "10:31:02", text: "СНС: Tauri HUD shell active", tone: "warn" },
  { time: "10:31:04", text: "СНС: local backend probe armed", tone: "" },
  { time: "10:31:05", text: "СНС: renderer: React + TypeScript", tone: "" },
  { time: "10:31:06", text: "СНС: desktop transport: loopback", tone: "" },
  { time: "10:31:12", text: "СНС: router: standby", tone: "" },
  { time: "10:31:13", text: "СНС: safety: local only", tone: "" },
];

function formatTime(date: Date): string {
  return date.toLocaleTimeString("ru-RU", { hour12: false });
}

function formatDate(date: Date): string {
  return date.toLocaleDateString("ru-RU", { day: "2-digit", month: "long", year: "numeric" }).toUpperCase();
}

export default function App() {
  const [backend, setBackend] = useState<BackendSnapshot>(initialBackend);
  const [now, setNow] = useState(() => new Date());
  const [command, setCommand] = useState("");
  const [listening, setListening] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [logs, setLogs] = useState<LogLine[]>(initialLogs);

  const metrics = useMemo(
    () => [
      { icon: "▣", name: "CPU", value: ["33%"], sub: "2.6 / 8 ядер", tone: "" },
      { icon: "▤", name: "MEM", value: ["74%"], sub: "11.8 / 16 GB", tone: "amber" },
      { icon: "◎", name: "NET", value: ["3.3 MB/s ↑", "1.1 MB/s ↓"], sub: "ОР0", tone: "green small" },
      { icon: "▦", name: "GPU", value: ["81%"], sub: "7.6 / 12 GB", tone: "amber" },
      { icon: "♨", name: "TEMP", value: ["54°C"], sub: "норма", tone: "red" },
    ],
    [],
  );

  const addLog = (text: string, tone: LogTone = "") => {
    setLogs((current) => [...current.slice(-34), { time: formatTime(new Date()), text, tone }]);
  };

  useEffect(() => {
    const interval = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const refresh = async () => {
      const snapshot = await readBackendSnapshot();
      if (cancelled) return;
      setBackend(snapshot);
      setLogs((current) => {
        const line = `СНС: backend ${snapshot.state} — ${snapshot.message}`;
        if (current[current.length - 1]?.text === line) return current;
        return [...current.slice(-34), { time: formatTime(new Date()), text: line, tone: snapshot.state === "connected" ? "" : "warn" }];
      });
    };

    void refresh();
    const interval = window.setInterval(refresh, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const submitCommand = () => {
    const value = command.trim();
    if (!value) return;
    addLog(`USER: ${value}`, "muted");
    setCommand("");
    window.setTimeout(() => addLog("СНС: команда принята — обработка..."), 180);
    window.setTimeout(() => addLog("СНС: готово."), 900);
  };

  const toggleListening = () => {
    setListening((current) => {
      addLog(`СНС: микрофон ${current ? "отключен" : "активирован"}`, current ? "warn" : "");
      return !current;
    });
  };

  const toggleFullscreen = () => {
    if (document.fullscreenElement) {
      void document.exitFullscreen();
      return;
    }
    void document.documentElement.requestFullscreen?.();
  };

  const onFiles = (files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach((file) => addLog(`FILE: ${file.name} [${Math.round(file.size / 1024)} KB]`));
  };

  return (
    <>
      <EnergyCanvas intensity={listening ? 1 : 0.45} />
      <div className="shell">
        <header className="topbar">
          <div className="brand"><div className="logo" /><div className="brandText">ПЕРСОНАЛЬНЫЙ<span>ИИ-АССИСТЕНТ</span></div></div>
          <div className="listen-pill"><span className="eqdot">···˙···</span><i className="live-dot" /><strong>{listening ? "СЛУШАЮ" : "ОЖИДАНИЕ"}</strong><span className="eqdot">···˙···</span></div>
          <div className="clockarea"><div className="clock"><b>{formatTime(now)}</b><small>{formatDate(now)}</small></div><button className="iconbtn" type="button" onClick={() => setSettingsOpen(true)} aria-label="Open settings">⌘</button><button className="iconbtn" type="button" aria-label="Theme">☼</button><button className="iconbtn" type="button" onClick={toggleFullscreen} aria-label="Toggle fullscreen">⛶</button></div>
        </header>

        <aside className="leftcol" aria-label="System monitor">
          <section className="panel monitor">
            <div className="panel-title"><span className="pulse-icon">⌁</span> МОНИТОР СИСТЕМЫ</div>
            {metrics.map((metric) => (
              <div className="metric" key={metric.name}>
                <div className="mi">{metric.icon}</div>
                <div className="name">{metric.name}</div>
                <div className={`value ${metric.tone}`}>{metric.value.map((part) => <span key={part}>{part}</span>)}</div>
                <div className="sub">{metric.sub}</div>
                <div className="mini" />
              </div>
            ))}
          </section>

          <section className="panel status">
            <div className="panel-title"><span className="pulse-icon">⌁</span> СТАТУС СИСТЕМЫ</div>
            <div className="kv">
              <div>РАБОТА</div><div className="green">14:18:07</div>
              <div>BACKEND</div><div>{backend.health ? "ONLINE" : "OFFLINE"}</div>
              <div>CONTROL</div><div>{backend.state === "unauthorized" ? "LOCKED" : backend.state.toUpperCase()}</div>
              <div>HOST</div><div>{backend.health ? `${backend.health.bind_host}:${backend.health.bind_port}` : "LOCAL"}</div>
            </div>
            <div className="statusbtn"><div className="ico">◉</div><div><b>ЯДРО ИИ</b><span>{backend.state === "offline" ? "ОЖИДАНИЕ" : "АКТИВНО"}</span></div></div>
            <div className="statusbtn"><div className="ico">♙</div><div><b>ДОСТУП</b><span>{backend.state === "unauthorized" ? "ТРЕБУЕТСЯ" : "РАЗРЕШЁН"}</span></div></div>
            <div className="statusbtn"><div className="ico">⬡</div><div><b>ПРОТОКОЛЫ</b><span>УСЛУГИ</span></div></div>
          </section>
          <div className="leftfoot"><button className="smallbtn" type="button">☷</button><button className="smallbtn" type="button">?</button><button className="smallbtn" type="button">☾</button></div>
        </aside>

        <main className="center" aria-label="Assistant core">
          <div className="core-wrap"><div className="core"><div className="tickring" /><div className="bars"><i /><i /><i /><i /><i /><i /><i /></div></div></div>
          <div className="micpod"><div className="wave" /><button className="mic" type="button" onClick={toggleListening} aria-label="Toggle microphone">🎙</button><div className="miclabel">ГОВОРИТЕ…<small>{listening ? "Я СЛУШАЮ" : "ОЖИДАНИЕ"}</small></div></div>
        </main>

        <aside className="rightcol" aria-label="Assistant controls">
          <section className="panel log"><div className="panel-title"><span className="pulse-icon">⌁</span> ЖУРНАЛ СОБЫТИЙ <div className="live"><i />LIVE</div></div><div className="logbody">{logs.map((line, index) => <div className={line.tone} key={`${line.time}-${index}`}><time>{line.time}</time>{line.text}</div>)}</div></section>
          <section className="panel drop"><div className="panel-title"><span className="pulse-icon">⌁</span> ЗАГРУЗКА ФАЙЛА</div><label className="dropzone"><input type="file" hidden multiple onChange={(event) => onFiles(event.currentTarget.files)} /><div><strong>♧</strong>Перетащите файл сюда или нажмите для выбора<small>Поддерживаются: .txt, .json, .pdf, .png, .mp4</small></div></label></section>
          <section className="panel command"><div className="panel-title"><span className="pulse-icon">⌁</span> ВВОД КОМАНДЫ</div><form className="cmdrow" onSubmit={(event) => { event.preventDefault(); submitCommand(); }}><input value={command} onChange={(event) => setCommand(event.target.value)} placeholder="Введите команду или вопрос..." /><button className="send" type="submit" disabled={!command.trim()} aria-label="Send command">›</button></form><button className={`toggle ${listening ? "active" : ""}`} type="button" onClick={toggleListening}>🎙 МИКРОФОН {listening ? "АКТИВЕН" : "ВЫКЛ"}</button><button className="toggle" type="button">⌁ ЛОКАЛЬНЫЙ TTS ВКЛ</button><button className="toggle" type="button">🔗 ЛОКАЛЬНЫЙ STT — СЛУШАТЬ</button><button className="toggle" type="button">▣ DESKTOP API {backend.health ? "ВКЛ" : "ВЫКЛ"}</button><button className="toggle" type="button" onClick={toggleFullscreen}>⛶ ПОЛНЫЙ ЭКРАН [F11]</button></section>
        </aside>
      </div>
      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}