import {
  Activity,
  ArrowRight,
  Boxes,
  Check,
  ChevronRight,
  CircleHelp,
  ClipboardCheck,
  Clock3,
  Download,
  FileText,
  Gauge,
  HeartHandshake,
  Inbox,
  LayoutDashboard,
  Leaf,
  LoaderCircle,
  MapPin,
  Mail,
  Play,
  RefreshCw,
  Route,
  Scale,
  Settings,
  ShieldCheck,
  Sparkles,
  TimerReset,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { Dashboard, Decision, Dispatch, Evidence, RunStep } from "./types";

const EMPTY: Dashboard = {
  active_run: null,
  dispatches: [],
  decisions: [],
  message_drafts: [],
  evidence: [],
  impact: { pounds_matched: 0, meals_estimated: 0, minutes_saved: 0 },
  run_history: [],
  intake_events: [],
};

const NAV = [
  { label: "Rescue desk", icon: LayoutDashboard, href: "#rescue-desk", active: true },
  { label: "Pickups", icon: Inbox, href: "#pickups" },
  { label: "Decisions", icon: Users, href: "#decisions" },
  { label: "Run trace", icon: Activity, href: "#run-trace" },
];

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 34 34" role="img">
        <path d="M5 11.5 17 5l12 6.5v12L17 30 5 23.5z" />
        <path d="m5 11.5 12 7 12-7M17 18.5V30M10.7 8.4l12.2 7" />
        <path className="brand-leaf" d="M19.5 8.8c1.6-3 4.1-3.5 6-3.2-.2 2.3-1.4 4.7-5.4 5.2" />
      </svg>
    </span>
  );
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <div>
        <div className="brand">
          <BrandMark />
          <div>
            <strong>RescueRelay</strong>
            <span>Community food rescue</span>
          </div>
        </div>
        <nav aria-label="Primary navigation">
          {NAV.map(({ label, icon: Icon, href, active }) => (
            <a className={active ? "nav-item active" : "nav-item"} href={href} key={label}>
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>
            </a>
          ))}
        </nav>
      </div>
      <div className="sidebar-bottom">
        <div className="agent-status">
          <span className="status-pulse" />
          <div>
            <strong>Replay ready</strong>
            <span>Event intake armed</span>
          </div>
        </div>
        <a className="nav-item" href="/api/health">
          <Settings size={18} strokeWidth={1.8} />
          <span>System status</span>
        </a>
      </div>
    </aside>
  );
}

function EmptyDesk({ onRun, loading }: { onRun: () => void; loading: boolean }) {
  return (
    <section className="empty-desk">
      <span className="empty-icon"><Inbox size={28} /></span>
      <p className="eyebrow">Demo workspace ready</p>
      <h2>Turn four donor messages into a safe pickup plan.</h2>
      <p>
        Simulate one inbox event. RescueRelay runs the real Strands tool loop quietly and surfaces only
        the decisions that need you. No messages are sent.
      </p>
      <button className="primary-button" onClick={onRun} disabled={loading} type="button">
        {loading ? <LoaderCircle className="spin" size={17} /> : <Play size={17} fill="currentColor" />}
        {loading ? "Agent is working…" : "Simulate offer arrival"}
      </button>
    </section>
  );
}

function RunTimeline({ steps, selected, onSelect }: {
  steps: RunStep[];
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  const icons = [Inbox, ClipboardCheck, Route, FileText];
  return (
    <section className="run-strip" aria-label="Latest agent run" id="run-trace">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Latest agent run</p>
          <h2>From offer to dispatch plan</h2>
        </div>
        <span className="mode-pill"><Sparkles size={12} /> event-triggered replay</span>
      </div>
      <div className="timeline">
        {steps.map((step, index) => {
          const Icon = icons[index] ?? Check;
          return (
            <button
              className={selected === step.id ? "timeline-step selected" : "timeline-step"}
              key={step.id}
              onClick={() => onSelect(step.id)}
              type="button"
            >
              <span className="step-icon"><Icon size={17} /></span>
              <span>
                <small>0{index + 1}</small>
                <strong>{step.label}</strong>
                <em>{step.duration_ms} ms</em>
              </span>
              {index < steps.length - 1 && <ChevronRight className="step-arrow" size={17} />}
            </button>
          );
        })}
      </div>
    </section>
  );
}

function EvidencePanel({ step, evidence }: { step: RunStep | undefined; evidence: Evidence[] }) {
  const linked = evidence.filter((item) => step?.evidence_ids.includes(item.id)).slice(0, 4);
  return (
    <section className="evidence-panel">
      <div className="step-detail">
        <p className="eyebrow">Selected step</p>
        <div className="detail-title">
          <span className="success-mark"><Check size={16} /></span>
          <div>
            <h3>{step?.label ?? "Choose a step"}</h3>
            <p>{step?.detail ?? "Inspect how the agent reached its plan."}</p>
          </div>
        </div>
        <div className="boundary-note">
          <ShieldCheck size={17} />
          <span><strong>Safe boundary:</strong> drafts only; the agent has no send tool.</span>
        </div>
      </div>
      <div className="evidence-list">
        <div className="evidence-header">
          <span>Linked evidence</span>
          <span>{linked.length} sources</span>
        </div>
        {linked.length ? linked.map((item) => (
          <article className="evidence-row" key={item.id}>
            {item.kind === "donor_message" ? <FileText size={16} /> : <Gauge size={16} />}
            <div>
              <strong>{item.label}</strong>
              <p>{item.detail}</p>
            </div>
          </article>
        )) : <p className="muted-copy">No source records linked to this step.</p>}
      </div>
    </section>
  );
}

function DispatchTable({ dispatches }: { dispatches: Dispatch[] }) {
  return (
    <section className="dispatch-section" id="pickups">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Ready to move</p>
          <h2>Today’s proposed pickups</h2>
        </div>
        <span className="count-label">{dispatches.length} offers matched</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Donor offer</th><th>Matched destination</th><th>Pickup</th><th>Confidence</th><th>Status</th></tr>
          </thead>
          <tbody>
            {dispatches.map((dispatch) => (
              <tr key={dispatch.id}>
                <td>
                  <strong>{dispatch.donor}</strong>
                  <span>
                    {dispatch.pounds} lb matched · {dispatch.description}
                    {dispatch.unallocated_pounds > 0 ? ` · ${dispatch.unallocated_pounds} lb unmatched` : ""}
                  </span>
                </td>
                <td>
                  <strong>{dispatch.allocations.map((a) => a.pantry_name).join(" + ")}</strong>
                  <span>{dispatch.allocations.map((a) => `${a.pounds} lb`).join(" / ")}</span>
                </td>
                <td><strong>{dispatch.pickup_window}</strong><span>local window</span></td>
                <td><span className="confidence"><i style={{ width: `${dispatch.confidence}%` }} />{dispatch.confidence}%</span></td>
                <td><span className={`state-badge ${dispatch.state}`}>{dispatch.state.replaceAll("_", " ")}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DraftPreview({ dashboard }: { dashboard: Dashboard }) {
  return (
    <section className="draft-section" aria-label="Staged message drafts">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Reversible work</p>
          <h2>Outreach staged, never sent</h2>
        </div>
        <span className="count-label">{dashboard.message_drafts.length} drafts</span>
      </div>
      <div className="draft-grid">
        {dashboard.message_drafts.slice(0, 2).map((draft) => (
          <article className="draft-card" key={draft.id}>
            <Mail size={17} />
            <div>
              <strong>{draft.subject}</strong>
              <span>To: {draft.recipient}</span>
              <p>{draft.body}</p>
            </div>
            <em>STAGED</em>
          </article>
        ))}
      </div>
    </section>
  );
}

function DecisionCard({ decision, onResolve, busy }: {
  decision: Decision;
  onResolve: (id: string, state: "approved" | "rejected") => void;
  busy: boolean;
}) {
  const approved = decision.state === "approved";
  const rejected = decision.state === "rejected";
  return (
    <article className={`decision-card ${decision.state}`}>
      <div className="decision-top">
        <span className="decision-icon">
          {approved ? <Check size={16} /> : rejected ? <X size={16} /> : <CircleHelp size={16} />}
        </span>
        <span>{approved ? "Approved" : rejected ? "Declined" : "Your call"}</span>
      </div>
      <h3>{decision.title}</h3>
      <p>{decision.context}</p>
      {decision.state === "pending" && (
        <div className="decision-actions">
          <button disabled={busy} onClick={() => onResolve(decision.id, "rejected")} type="button">
            Decline <X size={14} />
          </button>
          <button disabled={busy} onClick={() => onResolve(decision.id, "approved")} type="button">
            Approve <ArrowRight size={15} />
          </button>
        </div>
      )}
    </article>
  );
}

function DecisionRail({ dashboard, onResolve, busy }: {
  dashboard: Dashboard;
  onResolve: (id: string, state: "approved" | "rejected") => void;
  busy: boolean;
}) {
  const pending = dashboard.decisions.filter((item) => item.state === "pending").length;
  return (
    <aside className="decision-rail" id="decisions">
      <div className="rail-heading">
        <div>
          <p className="eyebrow">Needs you</p>
          <h2>{pending ? `${pending} decisions` : "All clear"}</h2>
        </div>
        <span className={pending ? "decision-count" : "decision-count clear"}>{pending}</span>
      </div>
      <p className="rail-intro">
        RescueRelay stays quiet until judgment or a real-world commitment is required.
      </p>
      <div className="decision-stack">
        {dashboard.decisions.map((decision) => (
          <DecisionCard decision={decision} key={decision.id} onResolve={onResolve} busy={busy} />
        ))}
      </div>
      <section className="impact-card">
        <div className="impact-title"><HeartHandshake size={18} /><span>Today’s impact</span></div>
        <div className="impact-primary">
          <strong>{dashboard.impact.pounds_matched}</strong>
          <span>lb matched</span>
        </div>
        <div className="impact-grid">
          <div><Scale size={16} /><strong>{dashboard.impact.meals_estimated}</strong><span>meals est.</span></div>
          <div><Clock3 size={16} /><strong>{dashboard.impact.minutes_saved}</strong><span>min saved</span></div>
        </div>
        <p><Leaf size={14} /> Estimated from completed allocations, never model-generated.</p>
      </section>
    </aside>
  );
}

export default function App() {
  const [dashboard, setDashboard] = useState<Dashboard>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStep, setSelectedStep] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard()
      .then((data) => {
        setDashboard(data);
        setSelectedStep(data.active_run?.steps.at(-1)?.id ?? null);
      })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not load desk"))
      .finally(() => setLoading(false));
  }, []);

  const step = useMemo(
    () => dashboard.active_run?.steps.find((item) => item.id === selectedStep),
    [dashboard.active_run, selectedStep],
  );

  async function runScan() {
    setLoading(true);
    setError(null);
    try {
      const eventId = `demo-${Date.now()}-${crypto.randomUUID()}`;
      await api.triggerDemoEvent(eventId);
      let event = await api.event(eventId);
      for (let attempt = 0; !["completed", "failed"].includes(event.status) && attempt < 100; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 100));
        event = await api.event(eventId);
      }
      if (event.status === "failed") throw new Error(`Background run failed: ${event.error}`);
      if (event.status !== "completed") throw new Error("Background run did not finish within 10 seconds");
      const data = await api.dashboard();
      setDashboard(data);
      setSelectedStep(data.active_run?.steps.at(-1)?.id ?? null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The run failed loudly");
    } finally {
      setLoading(false);
    }
  }

  async function resolve(id: string, state: "approved" | "rejected") {
    setLoading(true);
    try {
      setDashboard(await api.resolve(id, state));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Decision failed");
    } finally {
      setLoading(false);
    }
  }

  async function downloadAudit() {
    try {
      const audit = await api.audit();
      const url = URL.createObjectURL(new Blob([JSON.stringify(audit, null, 2)], { type: "application/json" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "rescue-relay-audit.json";
      link.click();
      URL.revokeObjectURL(url);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Audit export failed");
    }
  }

  async function reset() {
    setLoading(true);
    try {
      setDashboard(await api.reset());
      setSelectedStep(null);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Reset failed");
    } finally {
      setLoading(false);
    }
  }

  const hasRun = Boolean(dashboard.active_run);

  return (
    <div className="app-shell" id="rescue-desk">
      <Sidebar />
      <main>
        <header className="topbar">
          <div>
            <p className="date-line">Friday, August 28 · Good morning, Maya</p>
            <h1>Today’s rescue desk</h1>
            <p className="subtitle">One calm view of every offer, handoff, and decision.</p>
          </div>
          <div className="header-actions">
            <span className="demo-label"><ShieldCheck size={14} /> labeled demo data</span>
            {dashboard.intake_events[0] && (
              <span className="demo-label"><Activity size={14} /> event {dashboard.intake_events[0].status}</span>
            )}
            {hasRun && (
              <>
                <button className="icon-button" onClick={downloadAudit} title="Download audit evidence" type="button">
                  <Download size={17} />
                </button>
                <button className="icon-button" onClick={reset} title="Reset demo" type="button">
                  <RefreshCw size={17} />
                </button>
              </>
            )}
            <button className="primary-button" onClick={runScan} disabled={loading} type="button">
              {loading ? <LoaderCircle className="spin" size={17} /> : <Play size={17} fill="currentColor" />}
              {loading ? "Agent is working…" : hasRun ? "Simulate another event" : "Simulate offer arrival"}
            </button>
          </div>
        </header>

        {error && <div className="error-banner" role="alert"><ShieldCheck size={17} /><span>{error}</span></div>}

        {!hasRun ? <EmptyDesk onRun={runScan} loading={loading} /> : (
          <div className="workspace-grid">
            <div className="main-column">
              <RunTimeline
                steps={dashboard.active_run?.steps ?? []}
                selected={selectedStep}
                onSelect={setSelectedStep}
              />
              <EvidencePanel step={step} evidence={dashboard.evidence} />
              <DispatchTable dispatches={dashboard.dispatches} />
              <DraftPreview dashboard={dashboard} />
              <div className="run-footnote">
                <span><TimerReset size={14} /> Last run {new Date(dashboard.active_run!.completed_at ?? dashboard.active_run!.started_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</span>
                <span><Boxes size={14} /> {dashboard.active_run?.model_id}</span>
                <span>
                  <Activity size={14} /> Event {dashboard.intake_events[0]
                    ? `${dashboard.intake_events[0].source} · ${dashboard.intake_events[0].id.slice(0, 16)}…`
                    : "manual diagnostic"}
                </span>
                <span><MapPin size={14} /> Local demo workspace</span>
              </div>
            </div>
            <DecisionRail dashboard={dashboard} onResolve={resolve} busy={loading} />
          </div>
        )}
      </main>
    </div>
  );
}
