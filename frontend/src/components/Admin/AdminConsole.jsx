import { useCallback, useEffect, useState } from "react";
import {
  adminAiLogs, adminAiSummary, adminAuditLogs, adminCategories, adminExportComplaints, adminListUsers,
  adminOverview, adminSystem, adminUpdateUser, errorMessage,
} from "../../api";
import { roleLabel } from "../../utils/validation";
import "../../styles/Console.css";

const TABS = [
  ["overview", "Overview"], ["users", "Users & roles"], ["categories", "Categories"],
  ["ai", "AI monitoring"], ["audit", "Audit log"], ["system", "System"],
];
const DEPARTMENTS = ["", "Billing", "Technical", "Delivery", "Service", "Security", "Other"];

function useLoader(fn, deps) {
  const [state, setState] = useState({ loading: true, error: "", data: null });
  const run = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: "" }));
    try {
      setState({ loading: false, error: "", data: await fn() });
    } catch (err) {
      setState({ loading: false, error: errorMessage(err), data: null });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { run(); }, [run]);
  return [state, run];
}

function Status({ state, empty }) {
  if (state.loading) return <p className="qf-muted" role="status">Loading…</p>;
  if (state.error) return <p className="qf-error" role="alert">{state.error}</p>;
  if (empty) return <p className="qf-muted">Nothing to show yet.</p>;
  return null;
}

function Pager({ page, totalPages, onChange }) {
  if (!totalPages || totalPages <= 1) return null;
  return (
    <div className="qf-pager">
      <button type="button" disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</button>
      <span>Page {page} of {totalPages}</span>
      <button type="button" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>Next</button>
    </div>
  );
}

function Counts({ title, data }) {
  const entries = Object.entries(data || {});
  return (
    <div className="qf-card">
      <h3>{title}</h3>
      {entries.length === 0 ? <p className="qf-muted">No data</p> : (
        <ul className="qf-counts">{entries.map(([k, v]) => <li key={k}><span>{(k || "unknown").replace(/_/g, " ")}</span><strong>{v}</strong></li>)}</ul>
      )}
    </div>
  );
}

function Overview() {
  const [state] = useLoader(adminOverview, []);
  const d = state.data;
  return (
    <section aria-label="Overview">
      <Status state={state} />
      {d && (
        <>
          <div className="qf-stats">
            <div className="qf-stat"><span>Total complaints</span><strong>{d.complaints.total}</strong></div>
            <div className="qf-stat"><span>Need human review</span><strong>{d.complaints.needs_review}</strong></div>
            <div className="qf-stat"><span>Avg. resolution</span><strong>{d.complaints.avg_resolution_hours ?? "–"}{d.complaints.avg_resolution_hours != null && " h"}</strong></div>
            <div className="qf-stat"><span>Users</span><strong>{d.users.total}</strong></div>
            <div className="qf-stat"><span>AI analyses (30 days)</span><strong>{d.ai_last_30_days.analyses}</strong></div>
            <div className="qf-stat"><span>Offline fallbacks</span><strong>{d.ai_last_30_days.fallbacks}</strong></div>
          </div>
          <div className="qf-grid">
            <Counts title="By status" data={d.complaints.by_status} />
            <Counts title="By category" data={d.complaints.by_category} />
            <Counts title="By priority" data={d.complaints.by_priority} />
            <Counts title="Users by role" data={d.users.by_role} />
          </div>
          <div className="qf-card">
            <h3>Complaints per day (last 14 days)</h3>
            {d.complaints.daily.length === 0 ? <p className="qf-muted">No complaints in this period.</p> : (
              <ul className="qf-bars">
                {d.complaints.daily.map((day) => {
                  const max = Math.max(...d.complaints.daily.map((x) => x.count));
                  return (
                    <li key={day.date}><span>{day.date.slice(5)}</span>
                      <span className="qf-bar" style={{ width: `${(day.count / max) * 100}%` }} /><strong>{day.count}</strong></li>
                  );
                })}
              </ul>
            )}
          </div>
          <button type="button" className="qf-button" onClick={() => adminExportComplaints().catch(() => alert("Export failed"))}>
            Download complaints (CSV)
          </button>
        </>
      )}
    </section>
  );
}

function Users({ currentUserId }) {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState({ search: "", role: "", page: 1 });
  const [notice, setNotice] = useState("");
  const [state, reload] = useLoader(() => adminListUsers({ ...query, page_size: 20 }), [query]);

  const change = async (user, changes, confirmText) => {
    if (confirmText && !window.confirm(confirmText)) return;
    try {
      await adminUpdateUser(user.id, changes);
      setNotice(`Updated ${user.email}`);
      reload();
    } catch (err) {
      setNotice(errorMessage(err));
    }
  };

  const items = state.data?.items || [];
  return (
    <section aria-label="Users and roles">
      <form className="qf-toolbar" onSubmit={(e) => { e.preventDefault(); setQuery({ ...query, search, page: 1 }); }}>
        <label className="qf-sr" htmlFor="user-search">Search users</label>
        <input id="user-search" placeholder="Search name, email or phone" value={search} onChange={(e) => setSearch(e.target.value)} />
        <label className="qf-sr" htmlFor="user-role">Filter by role</label>
        <select id="user-role" value={query.role} onChange={(e) => setQuery({ ...query, role: e.target.value, page: 1 })}>
          <option value="">All roles</option><option value="customer">Customers</option>
          <option value="agent">Support agents</option><option value="admin">Admins</option>
        </select>
        <button type="submit" className="qf-button">Search</button>
      </form>
      <p className="qf-muted qf-small">Staff roles can only be given to verified accounts. Changing a role signs that user out everywhere.</p>
      {notice && <p className="qf-notice" role="status">{notice}</p>}
      <Status state={state} empty={!items.length} />
      {items.length > 0 && (
        <div className="qf-table-wrap">
          <table className="qf-table">
            <thead><tr><th>User</th><th>Mobile</th><th>Verified</th><th>Role</th><th>Department</th><th>Open tickets</th><th>Active</th></tr></thead>
            <tbody>
              {items.map((u) => (
                <tr key={u.id}>
                  <td data-label="User"><strong>{u.full_name || "—"}</strong><div className="qf-muted qf-small">{u.email}</div></td>
                  <td data-label="Mobile">{u.phone || <span className="qf-muted">missing</span>}</td>
                  <td data-label="Verified">{u.email_verified ? "Yes" : "No"}</td>
                  <td data-label="Role">
                    <select aria-label={`Role for ${u.email}`} value={u.role} disabled={u.id === currentUserId}
                      onChange={(e) => change(u, { role: e.target.value }, `Change ${u.email} to ${roleLabel(e.target.value)}?`)}>
                      <option value="customer">Customer</option><option value="agent">Support agent</option><option value="admin">Admin</option>
                    </select>
                  </td>
                  <td data-label="Department">
                    <select aria-label={`Department for ${u.email}`} value={u.department || ""} disabled={u.role !== "agent"}
                      onChange={(e) => change(u, { department: e.target.value })}>
                      {DEPARTMENTS.map((d) => <option key={d} value={d}>{d || "Any"}</option>)}
                    </select>
                  </td>
                  <td data-label="Open tickets">{u.open_assigned}</td>
                  <td data-label="Active">
                    <button type="button" className="qf-link" disabled={u.id === currentUserId}
                      onClick={() => change(u, { is_active: !u.is_active }, u.is_active ? `Disable ${u.email}? They will be signed out.` : null)}>
                      {u.is_active ? "Disable" : "Enable"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Pager page={query.page} totalPages={state.data?.total_pages} onChange={(page) => setQuery({ ...query, page })} />
    </section>
  );
}

function Categories() {
  const [state] = useLoader(adminCategories, []);
  const items = state.data?.items || [];
  return (
    <section aria-label="Categories">
      <p className="qf-muted qf-small">The AI classifies complaints into this fixed set. Agents with a matching department receive those tickets first.</p>
      <Status state={state} />
      {items.length > 0 && (
        <div className="qf-table-wrap"><table className="qf-table">
          <thead><tr><th>Category</th><th>Total</th><th>Open</th><th>Agents in department</th></tr></thead>
          <tbody>{items.map((c) => <tr key={c.name}><td data-label="Category">{c.name}</td><td data-label="Total">{c.total}</td><td data-label="Open">{c.open}</td><td data-label="Agents">{c.agents}</td></tr>)}</tbody>
        </table></div>
      )}
    </section>
  );
}

function AiMonitoring() {
  const [page, setPage] = useState(1);
  const [fallbackOnly, setFallbackOnly] = useState(false);
  const [summary] = useLoader(adminAiSummary, []);
  const [logs] = useLoader(() => adminAiLogs({ page, page_size: 25, fallback_only: fallbackOnly }), [page, fallbackOnly]);
  const items = logs.data?.items || [];
  return (
    <section aria-label="AI monitoring">
      <Status state={summary} />
      {summary.data && (
        <div className="qf-card">
          <h3>Models used</h3>
          <p className="qf-muted qf-small">{summary.data.complaints_requiring_review} of {summary.data.complaints_total} complaints were flagged for human review.</p>
          {summary.data.by_model.length === 0 ? <p className="qf-muted">No AI calls recorded yet.</p> : (
            <div className="qf-table-wrap"><table className="qf-table">
              <thead><tr><th>Operation</th><th>Provider</th><th>Model</th><th>Calls</th><th>Avg latency</th></tr></thead>
              <tbody>{summary.data.by_model.map((m, i) => (
                <tr key={i}><td data-label="Operation">{m.operation}</td><td data-label="Provider">{m.provider || "—"}</td><td data-label="Model">{m.model || "—"}</td>
                  <td data-label="Calls">{m.calls}</td><td data-label="Latency">{m.avg_latency_ms != null ? `${m.avg_latency_ms} ms` : "—"}</td></tr>))}
              </tbody>
            </table></div>
          )}
        </div>
      )}
      <label className="qf-check"><input type="checkbox" checked={fallbackOnly} onChange={(e) => { setFallbackOnly(e.target.checked); setPage(1); }} /> Only offline fallbacks</label>
      <Status state={logs} empty={!items.length} />
      {items.length > 0 && (
        <div className="qf-table-wrap"><table className="qf-table">
          <thead><tr><th>Time</th><th>Ticket</th><th>Operation</th><th>Model</th><th>Result</th><th>Latency</th></tr></thead>
          <tbody>{items.map((l) => (
            <tr key={l.id}><td data-label="Time">{new Date(l.created_at).toLocaleString()}</td><td data-label="Ticket">{l.ticket_id || "—"}</td>
              <td data-label="Operation">{l.operation}</td><td data-label="Model">{l.provider ? `${l.provider} / ${l.model || "?"}` : "—"}</td>
              <td data-label="Result">{l.fallback_used ? "Offline fallback" : l.success ? "OK" : "Failed"}{l.error && <div className="qf-muted qf-small">{l.error}</div>}</td>
              <td data-label="Latency">{l.latency_ms != null ? `${l.latency_ms} ms` : "—"}</td></tr>))}
          </tbody>
        </table></div>
      )}
      <Pager page={page} totalPages={logs.data?.total_pages} onChange={setPage} />
    </section>
  );
}

function Audit() {
  const [page, setPage] = useState(1);
  const [state] = useLoader(() => adminAuditLogs({ page, limit: 30 }), [page]);
  const items = state.data?.items || [];
  return (
    <section aria-label="Audit log">
      <Status state={state} empty={!items.length} />
      {items.length > 0 && (
        <div className="qf-table-wrap"><table className="qf-table">
          <thead><tr><th>Time</th><th>Staff member</th><th>Action</th><th>Ticket</th><th>IP</th></tr></thead>
          <tbody>{items.map((l) => (
            <tr key={l.id}><td data-label="Time">{new Date(l.timestamp).toLocaleString()}</td><td data-label="Staff">{l.actor_name || `#${l.agent_id}`}</td>
              <td data-label="Action">{l.action.replace(/_/g, " ")}</td><td data-label="Ticket">{l.ticket_id || "—"}</td><td data-label="IP">{l.ip_address || "—"}</td></tr>))}
          </tbody>
        </table></div>
      )}
      <Pager page={page} totalPages={state.data?.total_pages} onChange={setPage} />
    </section>
  );
}

function System() {
  const [state] = useLoader(adminSystem, []);
  const d = state.data;
  const row = (label, value) => <li key={label}><span>{label}</span><strong>{String(value)}</strong></li>;
  return (
    <section aria-label="System">
      <p className="qf-muted qf-small">Read-only. These values come from server environment variables; secrets are never shown.</p>
      <Status state={state} />
      {d && (
        <div className="qf-grid">
          <div className="qf-card"><h3>Database</h3><ul className="qf-counts">
            {row("Engine", d.database.engine)}{row("Target", d.database.target)}
            {row("Migrations applied", d.database.migrations_applied.join(", ") || "none")}
            {row("Pending", d.database.migrations_pending.join(", ") || "none")}</ul></div>
          <div className="qf-card"><h3>Email</h3><ul className="qf-counts">
            {row("Transport", d.email.transport)}{row("Configured", d.email.configured ? "yes" : "NO")}
            {row("From", d.email.from || "—")}{row("Staff notifications", d.email.admin_notifications ? "on" : "off")}</ul></div>
          <div className="qf-card"><h3>AI</h3><ul className="qf-counts">
            {row("Groq", d.ai.groq_configured ? "configured" : "missing")}{row("Gemini", d.ai.gemini_configured ? "configured" : "missing")}
            {row("Timeout", `${d.ai.timeout_seconds}s`)}{row("Auto-resolve delay", `${d.ai.auto_resolve_delay_seconds}s`)}
            {row("Auto-send confidence", d.ai.auto_resolve_min_confidence)}</ul></div>
          <div className="qf-card"><h3>Authentication</h3><ul className="qf-counts">
            {row("Access token", `${d.auth.access_token_minutes} min`)}{row("Refresh token", `${d.auth.refresh_token_days} days`)}
            {row("OTP validity", `${d.auth.otp_ttl_seconds}s`)}{row("OTP resend cooldown", `${d.auth.otp_resend_cooldown_seconds}s`)}
            {row("OTPs per hour", d.auth.otp_max_per_hour)}{row("Google sign-in", d.auth.google_sign_in ? "on" : "off")}</ul></div>
        </div>
      )}
    </section>
  );
}

export default function AdminConsole({ user }) {
  const [tab, setTab] = useState("overview");
  return (
    <div className="qf-console">
      <div className="qf-tabs" role="tablist" aria-label="Admin sections">
        {TABS.map(([id, label]) => (
          <button key={id} type="button" role="tab" aria-selected={tab === id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>
      <div role="tabpanel">
        {tab === "overview" && <Overview />}
        {tab === "users" && <Users currentUserId={user?.id} />}
        {tab === "categories" && <Categories />}
        {tab === "ai" && <AiMonitoring />}
        {tab === "audit" && <Audit />}
        {tab === "system" && <System />}
      </div>
    </div>
  );
}
