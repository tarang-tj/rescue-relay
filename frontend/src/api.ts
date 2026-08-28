import type { Dashboard } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  dashboard: () => request<Dashboard>("/api/dashboard"),
  scan: () => request<Dashboard>("/api/runs", { method: "POST", body: JSON.stringify({ mode: "demo" }) }),
  approve: (id: string) => request<Dashboard>(`/api/decisions/${id}/approve`, { method: "POST" }),
  resolve: (id: string, state: "approved" | "rejected") => request<Dashboard>(
    `/api/decisions/${id}/resolve`,
    { method: "POST", body: JSON.stringify({ state }) },
  ),
  audit: () => request<Record<string, unknown>>("/api/audit"),
  reset: () => request<Dashboard>("/api/reset", { method: "POST" }),
};
