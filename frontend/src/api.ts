import type { Dashboard, IntakeEvent, OfferEventResponse } from "./types";

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
  triggerDemoEvent: (eventId: string) => request<OfferEventResponse>("/api/events/offers", {
    method: "POST",
    body: JSON.stringify({ event_id: eventId, source: "demo_inbox", mode: "demo" }),
  }),
  event: (eventId: string) => request<IntakeEvent>(`/api/events/${eventId}`),
  approve: (id: string) => request<Dashboard>(`/api/decisions/${id}/approve`, { method: "POST" }),
  resolve: (id: string, state: "approved" | "rejected") => request<Dashboard>(
    `/api/decisions/${id}/resolve`,
    { method: "POST", body: JSON.stringify({ state }) },
  ),
  audit: () => request<Record<string, unknown>>("/api/audit"),
  reset: () => request<Dashboard>("/api/reset", { method: "POST" }),
};
