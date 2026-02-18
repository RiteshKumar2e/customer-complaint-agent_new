import { useState, useEffect } from "react";
import { getAgentQueue, getComplaintDetail, validateSolution, sendResolution, logoutUser } from "../../api";
import ThemeToggle from "../ThemeToggle";
import "../../styles/AgentModule.css";
import { motion, AnimatePresence } from "framer-motion";

export default function AgentModule({ user, onNavigate }) {
    const [queue, setQueue] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        status: "pending",
        priority: "",
        category: "",
        search: ""
    });
    const [selectedComplaint, setSelectedComplaint] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const [draftSolution, setDraftSolution] = useState("");
    const [validationResult, setValidationResult] = useState(null);
    const [isValidating, setIsValidating] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [stats, setStats] = useState({
        total: 0,
        pending: 0,
        critical: 0,
        avg_confidence: 0
    });

    useEffect(() => {
        if (user) {
            fetchQueue();
        }
    }, [user, filters]);

    const fetchQueue = async () => {
        setLoading(true);
        try {
            const data = await getAgentQueue(user.email, {
                status: filters.status,
                priority: filters.priority,
                category: filters.category,
                search: filters.search
            });
            setQueue(data.complaints || []);

            // Calculate stats for demonstration
            const total = data.total || 0;
            const critical = (data.complaints || []).filter(c => c.sentiment === 'Critical' || c.priority === 'High').length;
            setStats({
                total,
                pending: filters.status === 'pending' ? total : 0, // Simplified
                critical,
                avg_confidence: 94.2 // Mocked for UI
            });
        } catch (error) {
            console.error("Failed to fetch queue", error);
        } finally {
            setLoading(false);
        }
    };

    const handleOpenComplaint = async (complaint) => {
        setDetailLoading(true);
        try {
            const data = await getComplaintDetail(complaint.ticket_id, user.email);
            setSelectedComplaint(data.complaint);
            setDraftSolution(data.agent_resolution?.draft_solution || data.complaint.ai_solution || "");
            setValidationResult(data.agent_resolution ? {
                confidence_score: data.agent_resolution.confidence_score,
                approval_status: data.agent_resolution.validation_status,
                validation_results: data.agent_resolution.validation_results // This is simplified
            } : null);
        } catch (error) {
            console.error("Failed to fetch complaint detail", error);
        } finally {
            setDetailLoading(false);
        }
    };

    const handleValidate = async () => {
        if (!draftSolution.trim()) return;
        setIsValidating(true);
        setValidationResult(null);
        try {
            const result = await validateSolution(user.email, selectedComplaint.ticket_id, draftSolution);
            setValidationResult(result);
        } catch (error) {
            console.error("Validation failed", error);
        } finally {
            setIsValidating(false);
        }
    };

    const handleSend = async () => {
        if (!draftSolution.trim()) return;
        setIsSending(true);
        try {
            await sendResolution(user.email, selectedComplaint.ticket_id, draftSolution);
            setSelectedComplaint(null);
            fetchQueue();
            alert("Resolution sent successfully!");
        } catch (error) {
            console.error("Failed to send resolution", error);
        } finally {
            setIsSending(false);
        }
    };

    const getSentimentBadge = (sentiment) => {
        const s = (sentiment || "").toLowerCase();
        if (s === 'negative') return <span className="badge badge-negative">Negative</span>;
        if (s === 'critical') return <span className="badge badge-critical">Critical</span>;
        if (s === 'angry') return <span className="badge badge-angry">Angry</span>;
        return <span className="badge badge-neutral">{sentiment || 'Neutral'}</span>;
    };

    const getPriorityClass = (priority) => {
        const p = (priority || "").toLowerCase();
        return `priority-${p}`;
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
                        <button className="nav-btn active" onClick={() => onNavigate("agent-queue")}>
                            📥 Agent Queue
                        </button>
                        <button className="nav-btn" onClick={() => onNavigate("agent-resolutions")}>
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

            <div className="agent-banner">
                <motion.h1
                    className="agent-title"
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    Agent Resolution Module
                </motion.h1>
                <p className="agent-subtitle">Deep analysis & multi-model AI validation pipeline</p>
            </div>

            <div className="agent-content">
                <div className="agent-stats">
                    <motion.div className="stat-glow-card" whileHover={{ y: -5 }}>
                        <span className="stat-label">Queue Size</span>
                        <span className="stat-value">{stats.total}</span>
                    </motion.div>
                    <motion.div className="stat-glow-card" whileHover={{ y: -5 }}>
                        <span className="stat-label">Pending Review</span>
                        <span className="stat-value">{stats.pending}</span>
                    </motion.div>
                    <motion.div className="stat-glow-card" whileHover={{ y: -5 }}>
                        <span className="stat-label">Critical Issues</span>
                        <span className="stat-value" style={{ color: 'var(--agent-error)' }}>{stats.critical}</span>
                    </motion.div>
                    <motion.div className="stat-glow-card" whileHover={{ y: -5 }}>
                        <span className="stat-label">AI Consensus Score</span>
                        <span className="stat-value" style={{ color: 'var(--agent-accent)' }}>{stats.avg_confidence}%</span>
                    </motion.div>
                </div>

                <div className="agent-controls">
                    <div className="search-wrapper">
                        <i>🔍</i>
                        <input
                            type="text"
                            placeholder="Search by Ticket ID, User, or Content..."
                            value={filters.search}
                            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                        />
                    </div>
                    <div className="filter-group">
                        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
                            <option value="pending">Pending Review</option>
                            <option value="resolved">Resolved</option>
                            <option value="">All Status</option>
                        </select>
                        <select value={filters.priority} onChange={(e) => setFilters({ ...filters, priority: e.target.value })}>
                            <option value="">All Priority</option>
                            <option value="High">High Priority</option>
                            <option value="Medium">Medium Priority</option>
                            <option value="Low">Low Priority</option>
                        </select>
                        <select value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
                            <option value="">All Categories</option>
                            <option value="Technical">Technical</option>
                            <option value="Billing">Billing</option>
                            <option value="Delivery">Delivery</option>
                            <option value="Service">Service</option>
                        </select>
                    </div>
                </div>

                <div className="queue-table-container">
                    <table className="queue-table">
                        <thead>
                            <tr>
                                <th>Ticket ID</th>
                                <th>User Details</th>
                                <th>Category</th>
                                <th>Sentiment</th>
                                <th>Priority</th>
                                <th>Timestamp</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="7" style={{ textAlign: 'center', padding: '4rem' }}><div className="loader" style={{ margin: '0 auto' }}></div></td></tr>
                            ) : queue.length === 0 ? (
                                <tr><td colSpan="7" style={{ textAlign: 'center', padding: '4rem' }}>No complaints found in queue.</td></tr>
                            ) : (
                                queue.map(complaint => (
                                    <tr
                                        key={complaint.id}
                                        className="queue-row"
                                        onClick={() => handleOpenComplaint(complaint)}
                                    >
                                        <td><span className="ticket-id">{complaint.ticket_id}</span></td>
                                        <td>
                                            <div className="user-info">
                                                <span className="user-name">{complaint.user_name}</span>
                                                <span className="user-email">{complaint.user_email}</span>
                                            </div>
                                        </td>
                                        <td>{complaint.category}</td>
                                        <td>{getSentimentBadge(complaint.sentiment)}</td>
                                        <td><span className={getPriorityClass(complaint.priority)}>{complaint.priority}</span></td>
                                        <td><span className="user-email">{new Date(complaint.created_at).toLocaleString()}</span></td>
                                        <td><span className={`status-${complaint.status}`}>{complaint.status.replace('_', ' ')}</span></td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <AnimatePresence>
                {selectedComplaint && (
                    <div className="agent-modal-overlay">
                        <motion.div
                            className="agent-modal"
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                        >
                            <div className="modal-header">
                                <div>
                                    <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>
                                        Ticket {selectedComplaint.ticket_id} — Deep Analysis
                                    </h2>
                                    <p className="user-email">Reviewing complaint from {selectedComplaint.user_name}</p>
                                </div>
                                <button className="btn btn-outline" onClick={() => setSelectedComplaint(null)}>Close</button>
                            </div>

                            <div className="modal-body">
                                <div className="analysis-grid">
                                    <div className="analysis-panel">
                                        <div className="panel">
                                            <h3 className="panel-title"><span>📋</span> Complaint Details</h3>
                                            <div className="complaint-text-box">
                                                <strong>{selectedComplaint.subject}</strong>
                                                <p style={{ marginTop: '0.5rem' }}>{selectedComplaint.description}</p>
                                            </div>

                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                                <div>
                                                    <span className="stat-label">Category</span>
                                                    <p>{selectedComplaint.category}</p>
                                                </div>
                                                <div>
                                                    <span className="stat-label">AI Sentiment</span>
                                                    <p>{selectedComplaint.sentiment}</p>
                                                </div>
                                            </div>

                                            <div className="ai-hint">
                                                <strong>🤖 AI Suggestion:</strong>
                                                <p style={{ marginTop: '0.25rem' }}>{selectedComplaint.ai_solution}</p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="resolution-panel">
                                        <div className="panel">
                                            <h3 className="panel-title"><span>✍️</span> Compose Resolution</h3>
                                            <textarea
                                                className="solution-editor"
                                                placeholder="Write a clear, step-by-step resolution..."
                                                value={draftSolution}
                                                onChange={(e) => setDraftSolution(e.target.value)}
                                            ></textarea>

                                            <div style={{ marginTop: '1.5rem' }}>
                                                <button
                                                    className="btn btn-primary"
                                                    onClick={handleValidate}
                                                    disabled={isValidating || !draftSolution.trim()}
                                                    style={{ width: '100%', justifyContent: 'center' }}
                                                >
                                                    {isValidating ? <><div className="loader"></div> Validating Solution...</> : "Validate with Multi-Model Pipeline"}
                                                </button>
                                            </div>

                                            {validationResult && (
                                                <motion.div
                                                    className="validation-results"
                                                    initial={{ opacity: 0, y: 10 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                >
                                                    <div className="validation-header">
                                                        <span className="stat-label">Groq Multi-Model Consensus</span>
                                                        <span className={`badge ${validationResult.approval_status === 'approved' ? 'badge-positive' : 'badge-negative'}`}>
                                                            {validationResult.approval_status.toUpperCase()}
                                                        </span>
                                                    </div>

                                                    <div className="confidence-meter">
                                                        <motion.div
                                                            className="confidence-fill"
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${validationResult.confidence_score * 100}%` }}
                                                        ></motion.div>
                                                    </div>

                                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '1rem' }}>
                                                        <span>Agreement Score: {(validationResult.confidence_score * 100).toFixed(1)}%</span>
                                                        <span>Threshold: 85%</span>
                                                    </div>

                                                    <div className="models-grid">
                                                        {validationResult.validation_results?.map((res, idx) => (
                                                            <div key={idx} className={`model-card ${res.passed ? 'success' : 'fail'}`}>
                                                                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{res.model.split('-')[0]}</span>
                                                                <span>{res.passed ? '✅' : '❌'}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="modal-footer">
                                <button className="btn btn-outline" onClick={() => setSelectedComplaint(null)}>Discard Draft</button>
                                <button
                                    className="btn btn-success"
                                    onClick={handleSend}
                                    disabled={isSending || !draftSolution.trim()}
                                >
                                    {isSending ? <><div className="loader"></div> Delivering...</> : (validationResult?.approval_status === 'rejected' ? "Force Approve & Deliver" : "Approve & Deliver to User")}
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}
