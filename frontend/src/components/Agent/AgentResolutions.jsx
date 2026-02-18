import { useState, useEffect } from "react";
import { getAllResolutions, logoutUser } from "../../api";
import ThemeToggle from "../ThemeToggle";
import "../../styles/AgentModule.css";
import { motion } from "framer-motion";

export default function AgentResolutions({ user, onNavigate }) {
    const [resolutions, setResolutions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        search: ""
    });

    useEffect(() => {
        if (user) {
            fetchResolutions();
        }
    }, [user, filters]);

    const fetchResolutions = async () => {
        setLoading(true);
        try {
            const data = await getAllResolutions(user.email, { search: filters.search });
            setResolutions(data.resolutions || []);
        } catch (error) {
            console.error("Failed to fetch resolutions", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="agent-module">
            {/* Professional Navigation Header */}
            <header className="agent-header">
                <div className="header-content" style={{
                    maxWidth: '1400px',
                    margin: '0 auto',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '1rem 2rem'
                }}>
                    <div className="logo" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'inherit' }} onClick={() => onNavigate("landing")}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--agent-primary)" strokeWidth="3">
                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                        </svg>
                        <span style={{ fontWeight: 800 }}>Quickfix Agent</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.2rem' }}>
                        <ThemeToggle className="navbar-theme-toggle" />
                        <button className="nav-btn" onClick={() => onNavigate("admin")} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            📊 Back to Dashboard
                        </button>
                        <button className="nav-btn" onClick={() => onNavigate("agent-queue")}>
                            📥 Agent Queue
                        </button>
                        <button className="nav-btn active" onClick={() => onNavigate("agent-resolutions")}>
                            📜 Resolution Log
                        </button>
                        <button className="nav-btn nav-btn-error" onClick={() => {
                            logoutUser(user.email);
                            localStorage.removeItem("user");
                            window.location.reload();
                        }} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            🚪 Logout
                        </button>
                    </div>
                </div>
            </header>

            <div className="agent-banner" style={{ padding: '3rem 2rem' }}>
                <motion.h1
                    className="agent-title"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                >
                    Agent Verified Resolutions
                </motion.h1>
                <p className="agent-subtitle">Database of all human-verified and AI-validated solutions</p>
            </div>

            <div className="agent-content">
                <div className="agent-controls">
                    <div className="search-wrapper">
                        <i>🔍</i>
                        <input
                            type="text"
                            placeholder="Search by Agent Name, User Email, or Content..."
                            value={filters.search}
                            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                        />
                    </div>
                </div>

                <div className="queue-table-container">
                    <table className="queue-table">
                        <thead>
                            <tr>
                                <th>Ticket ID</th>
                                <th>Support Agent</th>
                                <th>Customer</th>
                                <th>Resolution Strategy</th>
                                <th>AI Validation</th>
                                <th>Sent Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="6" style={{ textAlign: 'center', padding: '4rem' }}><div className="loader" style={{ margin: '0 auto' }}></div></td></tr>
                            ) : resolutions.length === 0 ? (
                                <tr><td colSpan="6" style={{ textAlign: 'center', padding: '4rem' }}>No archived resolutions found.</td></tr>
                            ) : (
                                resolutions.map(res => (
                                    <tr key={res.id} className="queue-row">
                                        <td><span className="ticket-id">{res.ticket_id}</span></td>
                                        <td>
                                            <div className="user-info">
                                                <span className="user-name">{res.agent_name}</span>
                                                <span className="user-email">Verification Specialist</span>
                                            </div>
                                        </td>
                                        <td>
                                            <div className="user-info">
                                                <span className="user-name">{res.user_name}</span>
                                                <span className="user-email">{res.user_email}</span>
                                            </div>
                                        </td>
                                        <td>
                                            <div className="resolution-text-preview">
                                                {res.final_solution}
                                            </div>
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                                <span className="badge badge-positive" style={{ justifyContent: 'center' }}>
                                                    {(res.confidence_score * 100).toFixed(1)}% Consensus
                                                </span>
                                                <span className="validation-status-text">
                                                    {res.validation_status}
                                                </span>
                                            </div>
                                        </td>
                                        <td>
                                            <span className="user-email">
                                                {new Date(res.sent_at).toLocaleDateString()}<br />
                                                {new Date(res.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
