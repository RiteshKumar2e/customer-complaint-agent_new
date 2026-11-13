import { useCallback, useEffect, useRef, useState } from "react";
import { listNotifications, markAllNotificationsRead, markNotificationRead, errorMessage } from "../api";
import "../styles/Console.css";

const POLL_MS = 60000;

/** In-app notifications for the signed-in user (polled every minute while the tab is visible). */
export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ items: [], unread: 0 });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const panelRef = useRef(null);

  const load = useCallback(async () => {
    if (document.hidden) return;
    setLoading(true);
    try {
      setData(await listNotifications({ page_size: 15 }));
      setError("");
    } catch (err) {
      setError(errorMessage(err, "Could not load notifications"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  useEffect(() => {
    if (!open) return undefined;
    const onClick = (e) => { if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onClick); document.removeEventListener("keydown", onKey); };
  }, [open]);

  const readOne = async (n) => {
    if (n.is_read) return;
    try {
      await markNotificationRead(n.id);
      setData((d) => ({ ...d, unread: Math.max(0, d.unread - 1), items: d.items.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)) }));
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const readAll = async () => {
    try {
      await markAllNotificationsRead();
      setData((d) => ({ ...d, unread: 0, items: d.items.map((x) => ({ ...x, is_read: true })) }));
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div className="qf-bell" ref={panelRef}>
      <button type="button" className="qf-bell-button" aria-label={`Notifications${data.unread ? `, ${data.unread} unread` : ""}`}
        aria-expanded={open} onClick={() => { setOpen(!open); if (!open) load(); }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {data.unread > 0 && <span className="qf-bell-count">{data.unread > 99 ? "99+" : data.unread}</span>}
      </button>
      {open && (
        <div className="qf-bell-panel" role="dialog" aria-label="Notifications">
          <div className="qf-bell-head">
            <strong>Notifications</strong>
            {data.unread > 0 && <button type="button" className="qf-link" onClick={readAll}>Mark all read</button>}
          </div>
          {error && <p className="qf-error" role="alert">{error}</p>}
          {loading && !data.items.length && <p className="qf-muted">Loading…</p>}
          {!loading && !error && !data.items.length && <p className="qf-muted">You're all caught up.</p>}
          <ul className="qf-bell-list">
            {data.items.map((n) => (
              <li key={n.id}>
                <button type="button" className={`qf-bell-item ${n.is_read ? "" : "unread"}`} onClick={() => readOne(n)}>
                  <span className="qf-bell-title">{n.title}</span>
                  <span className="qf-bell-msg">{n.message}</span>
                  <span className="qf-muted qf-small">{n.created_at ? new Date(n.created_at).toLocaleString() : ""}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
