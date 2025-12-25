import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getAllComplaints, deleteAllComplaints } from "../api";
import "../styles/AdminDashboard.css";

export default function AdminDashboard({ user, onNavigate, onLogout }) {
    const [complaints, setComplaints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [filterCategory, setFilterCategory] = useState("All");
    const [filterPriority, setFilterPriority] = useState("All");
    const [filterStatus, setFilterStatus] = useState("All");
    const [sortBy, setSortBy] = useState("date-desc");
    const [selectedComplaint, setSelectedComplaint] = useState(null);
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 10;

    useEffect(() => {
        loadAllComplaints();
    }, []);

    const loadAllComplaints = async () => {
        if (!user?.email) return;
        try {
            setLoading(true);
            const response = await fetch(`${import.meta.env.VITE_API_URL}/complaints?email=${encodeURIComponent(user.email)}`);
            const data = await response.json();
            setComplaints(data.complaints || []);
        } catch (error) {
            console.error("Error loading complaints:", error);
        } finally {
            setLoading(false);
        }
    };

    // Filter and sort logic
    const filteredComplaints = complaints.filter(complaint => {
        const matchesSearch =
            complaint.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            complaint.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            complaint.ticket_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            complaint.complaint_text?.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesCategory = filterCategory === "All" || complaint.category === filterCategory;
        const matchesPriority = filterPriority === "All" || complaint.priority === filterPriority;
        const matchesStatus = filterStatus === "All" ||
            (filterStatus === "Resolved" && complaint.is_resolved) ||
            (filterStatus === "Pending" && !complaint.is_resolved);

        return matchesSearch && matchesCategory && matchesPriority && matchesStatus;
    });

    const sortedComplaints = [...filteredComplaints].sort((a, b) => {
        switch (sortBy) {
            case "date-desc":
                return new Date(b.created_at) - new Date(a.created_at);
            case "date-asc":
                return new Date(a.created_at) - new Date(b.created_at);
            case "priority":
                const priorityOrder = { High: 3, Medium: 2, Low: 1 };
                return priorityOrder[b.priority] - priorityOrder[a.priority];
            case "name":
                return a.name?.localeCompare(b.name);
            default:
                return 0;
        }
    });

    // Pagination
    const totalPages = Math.ceil(sortedComplaints.length / itemsPerPage);
    const paginatedComplaints = sortedComplaints.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    // Stats
    const stats = {
        total: complaints.length,
        resolved: complaints.filter(c => c.is_resolved).length,
        pending: complaints.filter(c => !c.is_resolved).length,
        high: complaints.filter(c => c.priority === "High").length,
        categories: {
            Technical: complaints.filter(c => c.category === "Technical").length,
            Billing: complaints.filter(c => c.category === "Billing").length,
            Delivery: complaints.filter(c => c.category === "Delivery").length,
            Service: complaints.filter(c => c.category === "Service").length,
            Security: complaints.filter(c => c.category === "Security").length,
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="admin-dashboard">
            {/* Header */}
            <motion.header
                className="admin-header"
                initial={{ y: -100 }}
                animate={{ y: 0 }}
                transition={{ type: "spring", stiffness: 100 }}
            >
                <div className="admin-header-content">
                    <div className="admin-header-left">
                        <motion.div
                            className="admin-logo"
                            whileHover={{ scale: 1.05, rotate: 5 }}
                            onClick={() => onNavigate("landing")}
                        >
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                                <path d="M2 17l10 5 10-5" />
                                <path d="M2 12l10 5 10-5" />
                            </svg>
                            <span>QuickFix Admin</span>
                        </motion.div>
                    </div>

                    <div className="admin-header-right">
                        <motion.button
                            className="admin-profile-btn"
                            whileHover={{ scale: 1.05 }}
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                        >
                            <div className="admin-avatar">
                                {user?.profile_image ? (
                                    <img src={user.profile_image} alt={user.full_name} />
                                ) : (
                                    <div className="admin-avatar-placeholder">
                                        {user?.full_name?.charAt(0).toUpperCase() || "A"}
                                    </div>
                                )}
                            </div>
                            <span className="admin-name">{user?.full_name || "Admin"}</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="6 9 12 15 18 9" />
                            </svg>
                        </motion.button>

                        <AnimatePresence>
                            {isMenuOpen && (
                                <motion.div
                                    className="admin-dropdown"
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -10 }}
                                >
                                    <button onClick={() => { onNavigate("profile"); setIsMenuOpen(false); }}>
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                            <circle cx="12" cy="7" r="4" />
                                        </svg>
                                        My Profile
                                    </button>
                                    <div className="admin-dropdown-divider" />
                                    <button className="admin-logout-btn" onClick={onLogout}>
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                            <polyline points="16 17 21 12 16 7" />
                                            <line x1="21" y1="12" x2="9" y2="12" />
                                        </svg>
                                        Logout
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </motion.header>

            {/* Main Content */}
            <main className="admin-main">
                <div className="admin-container">
                    {/* Page Title */}
                    <motion.div
                        className="admin-page-header"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <h1 className="admin-page-title">Complaints Management</h1>
                        <p className="admin-page-subtitle">Monitor and manage all customer complaints</p>
                    </motion.div>

                    {/* Stats Grid */}
                    <motion.div
                        className="admin-stats-grid"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        <motion.div className="admin-stat-card" whileHover={{ y: -5 }}>
                            <div className="admin-stat-icon total">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                    <polyline points="14 2 14 8 20 8" />
                                </svg>
                            </div>
                            <div className="admin-stat-info">
                                <p className="admin-stat-label">Total Complaints</p>
                                <h3 className="admin-stat-value">{stats.total}</h3>
                            </div>
                        </motion.div>

                        <motion.div className="admin-stat-card" whileHover={{ y: -5 }}>
                            <div className="admin-stat-icon pending">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                    <polyline points="12 6 12 12 16 14" />
                                </svg>
                            </div>
                            <div className="admin-stat-info">
                                <p className="admin-stat-label">Pending</p>
                                <h3 className="admin-stat-value">{stats.pending}</h3>
                            </div>
                        </motion.div>

                        <motion.div className="admin-stat-card" whileHover={{ y: -5 }}>
                            <div className="admin-stat-icon resolved">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                    <polyline points="22 4 12 14.01 9 11.01" />
                                </svg>
                            </div>
                            <div className="admin-stat-info">
                                <p className="admin-stat-label">Resolved</p>
                                <h3 className="admin-stat-value">{stats.resolved}</h3>
                            </div>
                        </motion.div>

                        <motion.div className="admin-stat-card" whileHover={{ y: -5 }}>
                            <div className="admin-stat-icon high">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                    <line x1="12" y1="8" x2="12" y2="12" />
                                    <line x1="12" y1="16" x2="12.01" y2="16" />
                                </svg>
                            </div>
                            <div className="admin-stat-info">
                                <p className="admin-stat-label">High Priority</p>
                                <h3 className="admin-stat-value">{stats.high}</h3>
                            </div>
                        </motion.div>
                    </motion.div>

                    {/* Filters and Search */}
                    <motion.div
                        className="admin-filters"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <div className="admin-search-box">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="11" cy="11" r="8" />
                                <path d="m21 21-4.35-4.35" />
                            </svg>
                            <input
                                type="text"
                                placeholder="Search by name, email, ticket ID..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>

                        <div className="admin-filter-group">
                            <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
                                <option value="All">All Categories</option>
                                <option value="Technical">Technical</option>
                                <option value="Billing">Billing</option>
                                <option value="Delivery">Delivery</option>
                                <option value="Service">Service</option>
                                <option value="Security">Security</option>
                            </select>

                            <select value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}>
                                <option value="All">All Priorities</option>
                                <option value="High">High</option>
                                <option value="Medium">Medium</option>
                                <option value="Low">Low</option>
                            </select>

                            <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                                <option value="All">All Status</option>
                                <option value="Pending">Pending</option>
                                <option value="Resolved">Resolved</option>
                            </select>

                            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                                <option value="date-desc">Newest First</option>
                                <option value="date-asc">Oldest First</option>
                                <option value="priority">Priority</option>
                                <option value="name">Name (A-Z)</option>
                            </select>
                        </div>
                    </motion.div>

                    {/* Complaints Table */}
                    <motion.div
                        className="admin-table-container"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        {loading ? (
                            <div className="admin-loading">
                                <div className="admin-spinner" />
                                <p>Loading complaints...</p>
                            </div>
                        ) : paginatedComplaints.length === 0 ? (
                            <div className="admin-empty">
                                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                    <circle cx="12" cy="12" r="10" />
                                    <line x1="12" y1="8" x2="12" y2="12" />
                                    <line x1="12" y1="16" x2="12.01" y2="16" />
                                </svg>
                                <h3>No complaints found</h3>
                                <p>Try adjusting your filters or search terms</p>
                            </div>
                        ) : (
                            <>
                                <div className="admin-table-wrapper">
                                    <table className="admin-table">
                                        <thead>
                                            <tr>
                                                <th>Ticket ID</th>
                                                <th>Customer</th>
                                                <th>Email</th>
                                                <th>Category</th>
                                                <th>Priority</th>
                                                <th>Status</th>
                                                <th>Date</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {paginatedComplaints.map((complaint, index) => (
                                                <motion.tr
                                                    key={complaint.id}
                                                    initial={{ opacity: 0, x: -20 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: index * 0.05 }}
                                                    whileHover={{ backgroundColor: "rgba(139, 92, 246, 0.05)" }}
                                                >
                                                    <td>
                                                        <span className="admin-ticket-id">{complaint.ticket_id || `#${complaint.id}`}</span>
                                                    </td>
                                                    <td>
                                                        <div className="admin-customer-cell">
                                                            <div className="admin-customer-avatar">
                                                                {complaint.name?.charAt(0).toUpperCase() || "U"}
                                                            </div>
                                                            <span className="admin-customer-name">{complaint.name || "Unknown"}</span>
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <span className="admin-email">{complaint.email}</span>
                                                    </td>
                                                    <td>
                                                        <span className={`admin-badge admin-badge-${complaint.category?.toLowerCase()}`}>
                                                            {complaint.category}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <span className={`admin-priority admin-priority-${complaint.priority?.toLowerCase()}`}>
                                                            {complaint.priority}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <span className={`admin-status ${complaint.is_resolved ? 'resolved' : 'pending'}`}>
                                                            {complaint.is_resolved ? "Resolved" : "Pending"}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <span className="admin-date">{formatDate(complaint.created_at)}</span>
                                                    </td>
                                                    <td>
                                                        <motion.button
                                                            className="admin-view-btn"
                                                            whileHover={{ scale: 1.1 }}
                                                            whileTap={{ scale: 0.95 }}
                                                            onClick={() => setSelectedComplaint(complaint)}
                                                        >
                                                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                                                <circle cx="12" cy="12" r="3" />
                                                            </svg>
                                                        </motion.button>
                                                    </td>
                                                </motion.tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {/* Pagination */}
                                {totalPages > 1 && (
                                    <div className="admin-pagination">
                                        <button
                                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                            disabled={currentPage === 1}
                                        >
                                            Previous
                                        </button>
                                        <span className="admin-page-info">
                                            Page {currentPage} of {totalPages}
                                        </span>
                                        <button
                                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                            disabled={currentPage === totalPages}
                                        >
                                            Next
                                        </button>
                                    </div>
                                )}
                            </>
                        )}
                    </motion.div>
                </div>
            </main>

            {/* Complaint Detail Modal */}
            <AnimatePresence>
                {selectedComplaint && (
                    <motion.div
                        className="admin-modal-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setSelectedComplaint(null)}
                    >
                        <motion.div
                            className="admin-modal"
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="admin-modal-header">
                                <h2>Complaint Details</h2>
                                <button onClick={() => setSelectedComplaint(null)}>
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <line x1="18" y1="6" x2="6" y2="18" />
                                        <line x1="6" y1="6" x2="18" y2="18" />
                                    </svg>
                                </button>
                            </div>

                            <div className="admin-modal-content">
                                <div className="admin-modal-section">
                                    <h3>Customer Information</h3>
                                    <div className="admin-modal-grid">
                                        <div className="admin-modal-field">
                                            <label>Ticket ID</label>
                                            <p>{selectedComplaint.ticket_id || `#${selectedComplaint.id}`}</p>
                                        </div>
                                        <div className="admin-modal-field">
                                            <label>Customer Name</label>
                                            <p>{selectedComplaint.name}</p>
                                        </div>
                                        <div className="admin-modal-field">
                                            <label>Email</label>
                                            <p>{selectedComplaint.email}</p>
                                        </div>
                                        <div className="admin-modal-field">
                                            <label>Date Submitted</label>
                                            <p>{formatDate(selectedComplaint.created_at)}</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="admin-modal-section">
                                    <h3>Complaint Details</h3>
                                    <div className="admin-modal-grid">
                                        <div className="admin-modal-field">
                                            <label>Category</label>
                                            <span className={`admin-badge admin-badge-${selectedComplaint.category?.toLowerCase()}`}>
                                                {selectedComplaint.category}
                                            </span>
                                        </div>
                                        <div className="admin-modal-field">
                                            <label>Priority</label>
                                            <span className={`admin-priority admin-priority-${selectedComplaint.priority?.toLowerCase()}`}>
                                                {selectedComplaint.priority}
                                            </span>
                                        </div>
                                        <div className="admin-modal-field">
                                            <label>Status</label>
                                            <span className={`admin-status ${selectedComplaint.is_resolved ? 'resolved' : 'pending'}`}>
                                                {selectedComplaint.is_resolved ? "Resolved" : "Pending"}
                                            </span>
                                        </div>
                                        <div className="admin-modal-field">
                                            <label>Sentiment</label>
                                            <p>{selectedComplaint.sentiment || "N/A"}</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="admin-modal-section">
                                    <h3>Complaint Text</h3>
                                    <div className="admin-modal-text">
                                        {selectedComplaint.complaint_text}
                                    </div>
                                </div>

                                <div className="admin-modal-section">
                                    <h3>AI Response</h3>
                                    <div className="admin-modal-text">
                                        {selectedComplaint.response || "No response generated"}
                                    </div>
                                </div>

                                {selectedComplaint.solution && (
                                    <div className="admin-modal-section">
                                        <h3>Proposed Solution</h3>
                                        <div className="admin-modal-text">
                                            {selectedComplaint.solution}
                                        </div>
                                    </div>
                                )}

                                {selectedComplaint.action && (
                                    <div className="admin-modal-section">
                                        <h3>Recommended Action</h3>
                                        <div className="admin-modal-text">
                                            {selectedComplaint.action}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
