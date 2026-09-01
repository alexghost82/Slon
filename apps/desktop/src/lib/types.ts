export type BackendState = "starting" | "connected" | "offline" | "unauthorized" | "error";

export type AssistantState =
  | "idle"
  | "listening"
  | "thinking"
  | "speaking"
  | "muted"
  | "missingApiKey"
  | "error"
  | "offline";

export interface HealthResponse {
  status: "ok" | "starting" | string;
  uptime_seconds: number;
  tls: boolean;
  bind_host: string;
  bind_port: number;
}

export interface StatusResponse {
  [key: string]: unknown;
}

export interface BackendSnapshot {
  state: BackendState;
  health: HealthResponse | null;
  status: StatusResponse | null;
  message: string;
  checkedAt: string;
}

export interface ActivityItem {
  label: string;
  value: string;
  tone?: "primary" | "violet" | "success" | "warning" | "muted";
}