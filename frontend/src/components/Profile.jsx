import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { updateProfile, deleteAllComplaints, getAllComplaints, submitFeedback } from "../api";
import "../styles/Profile.css";

export default function Profile({ user, onNavigate, onLogout, complaints = [], setComplaints }) {
    const [activeTab, setActiveTab] = useState("dashboard");
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [updatingImage, setUpdatingImage] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [isEditingProfile, setIsEditingProfile] = useState(false);
    const [profileForm, setProfileForm] = useState({
        full_name: user?.full_name || "",
        phone: user?.phone || "",
        organization: user?.organization || "",
        bio: user?.bio || "",
        location: user?.location || "India",
        role: user?.role || "Strategic Member"
    });

    // Feedback states
    const [feedbackForm, setFeedbackForm] = useState({
        name: user?.full_name || "",
        email: user?.email || "",
        rating: "5",
        recommendation: "10",
        message: ""
    });
    const [feedbackLoading, setFeedbackLoading] = useState(false);
    const [feedbackSuccess, setFeedbackSuccess] = useState(false);
    const [feedbackError, setFeedbackError] = useState("");

    // Get user stats
    const totalComplaints = complaints.length;
    const resolvedComplaints = complaints.filter(c => c.is_resolved).length;
    const pendingComplaints = totalComplaints - resolvedComplaints;
    const highPriorityCount = complaints.filter(c => c.priority === "High").length;

    const categories = { Billing: 0, Technical: 0, Delivery: 0, Service: 0, Security: 0, Other: 0 };
    complaints.forEach(c => {
        if (categories.hasOwnProperty(c.category)) {
            categories[c.category]++;
        } else {
            categories.Other++;
        }
    });

    const handleImageUpdate = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > 5 * 1024 * 1024) {
            alert("Image size should be less than 5MB");
            return;
        }

        const reader = new FileReader();
        reader.onloadend = async () => {
            const base64String = reader.result;
            setUpdatingImage(true);
            try {
                const updatedUser = await updateProfile(user.email, { profile_image: base64String });
                localStorage.setItem("user", JSON.stringify(updatedUser));
                window.location.reload(); // Refresh to update user in App.jsx
            } catch (error) {
                console.error("Error updating profile image:", error);
                alert("Failed to update profile image");
            } finally {
                setUpdatingImage(false);
            }
        };
        reader.readAsDataURL(file);
    };

    const handleDeleteUserComplaints = async () => {
        if (!showDeleteConfirm) {
            setShowDeleteConfirm(true);
            return;
        }

        setIsDeleting(true);
        try {
            console.log("🗑️ Attempting to delete complaints for:", user?.email);
            const result = await deleteAllComplaints(user?.email);
            console.log("📡 API Result:", result);

            setComplaints([]);
            setShowDeleteConfirm(false);
            alert("All complaints have been successfully deleted.");
            console.log("✅ Complaints deleted successfully");
        } catch (error) {
            console.error("❌ Error deleting complaints:", error);
            alert("Failed to delete complaints: " + (error.response?.data?.detail || error.message));
        } finally {
            setIsDeleting(false);
        }
    };

    const handleProfileUpdate = async (e) => {
        e.preventDefault();
        try {
            const updatedUser = await updateProfile(user.email, profileForm);
            localStorage.setItem("user", JSON.stringify(updatedUser));
            setIsEditingProfile(false);
            window.location.reload(); // App.jsx persistence will keep us on profile
        } catch (error) {
            console.error("Error updating profile:", error);
            alert("Failed to update profile");
        }
    };

    const handleFeedbackSubmit = async (e) => {
        e.preventDefault();
        if (!feedbackForm.message.trim()) {
            setFeedbackError("Please enter your message");
            return;
        }

        setFeedbackLoading(true);
        setFeedbackError("");

        try {
            await submitFeedback({
                name: feedbackForm.name,
                email: feedbackForm.email,
                rating: parseInt(feedbackForm.rating),
                message: feedbackForm.message
            });

            setFeedbackSuccess(true);

            // Redirect to dashboard after 3 seconds
            setTimeout(() => {
                setFeedbackSuccess(false);
                setFeedbackForm(prev => ({ ...prev, message: "" }));
                setActiveTab("dashboard");
            }, 3000);
        } catch (error) {
            console.error("Feedback error:", error);
            setFeedbackError("Failed to send feedback. Please try again.");
        } finally {
            setFeedbackLoading(false);
        }
    };

    return (
        <div className="profile-container">
            {/* Header */}
            <motion.header
                className="profile-header"
                initial={{ y: -100 }}
                animate={{ y: 0 }}
                transition={{ type: "spring", stiffness: 100 }}
            >
                <div className="header-content">
                    <div className="header-left">
                        <motion.div
                            className="logo"
                            whileHover={{ scale: 1.05, rotate: 5 }}
                            onClick={() => onNavigate("landing")}
                            style={{ cursor: "pointer" }}
                        >
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                                <path d="M2 17l10 5 10-5" />
                                <path d="M2 12l10 5 10-5" />
                            </svg>
                            <span>QuickFix AI</span>
                        </motion.div>
                    </div>

                    <nav className="header-nav desktop-nav">
                        <motion.button
                            className={`nav-btn ${activeTab === "dashboard" ? "active" : ""}`}
                            onClick={() => setActiveTab("dashboard")}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <rect x="3" y="3" width="7" height="7" />
                                <rect x="14" y="3" width="7" height="7" />
                                <rect x="14" y="14" width="7" height="7" />
                                <rect x="3" y="14" width="7" height="7" />
                            </svg>
                            Dashboard
                        </motion.button>
                        <motion.button
                            className={`nav-btn ${activeTab === "profile" ? "active" : ""}`}
                            onClick={() => setActiveTab("profile")}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                <circle cx="12" cy="7" r="4" />
                            </svg>
                            Profile
                        </motion.button>
                        <motion.button
                            className={`nav-btn ${activeTab === "complaints" ? "active" : ""}`}
                            onClick={() => setActiveTab("complaints")}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                <polyline points="14 2 14 8 20 8" />
                                <line x1="16" y1="13" x2="8" y2="13" />
                                <line x1="16" y1="17" x2="8" y2="17" />
                                <polyline points="10 9 9 9 8 9" />
                            </svg>
                            My Complaints
                        </motion.button>
                        <motion.button
                            className={`nav-btn ${activeTab === "feedback" ? "active" : ""}`}
                            onClick={() => setActiveTab("feedback")}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                            </svg>
                            Feedback
                        </motion.button>
                        {user?.role === "Admin" && (
                            <motion.button
                                className="nav-btn admin-panel-btn"
                                onClick={() => onNavigate("admin")}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                style={{ color: "var(--secondary)", borderColor: "var(--secondary)" }}
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                                </svg>
                                Admin Panel
                            </motion.button>
                        )}
                    </nav>

                    <div className="header-right">
                        <motion.button
                            className="profile-btn"
                            whileHover={{ scale: 1.05 }}
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                        >
                            <div className="profile-avatar">
                                {user?.profile_image ? (
                                    <img src={user.profile_image} alt={user.full_name} />
                                ) : (
                                    <div className="avatar-placeholder">
                                        {user?.full_name?.charAt(0).toUpperCase() || "U"}
                                    </div>
                                )}
                            </div>
                            <span className="profile-name">{user?.full_name || "User"}</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="6 9 12 15 18 9" />
                            </svg>
                        </motion.button>

                        {/* Mobile Menu Toggle */}
                        <button
                            className="mobile-menu-toggle"
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                        >
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="3" y1="12" x2="21" y2="12" />
                                <line x1="3" y1="6" x2="21" y2="6" />
                                <line x1="3" y1="18" x2="21" y2="18" />
                            </svg>
                        </button>

                        <AnimatePresence>
                            {isMenuOpen && (
                                <motion.div
                                    className="dropdown-menu"
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -10 }}
                                >
                                    <button onClick={() => { setActiveTab("profile"); setIsMenuOpen(false); }}>
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                            <circle cx="12" cy="7" r="4" />
                                        </svg>
                                        My Profile
                                    </button>
                                    <button onClick={() => { setActiveTab("dashboard"); setIsMenuOpen(false); }}>
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <rect x="3" y="3" width="7" height="7" />
                                            <rect x="14" y="3" width="7" height="7" />
                                            <rect x="14" y="14" width="7" height="7" />
                                            <rect x="3" y="14" width="7" height="7" />
                                        </svg>
                                        Dashboard
                                    </button>
                                    <button onClick={() => { setActiveTab("complaints"); setIsMenuOpen(false); }}>
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                            <polyline points="14 2 14 8 20 8" />
                                        </svg>
                                        My Complaints
                                    </button>
                                    <button onClick={() => { setActiveTab("feedback"); setIsMenuOpen(false); }}>
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                                        </svg>
                                        Send Feedback
                                    </button>
                                    <div className="dropdown-divider"></div>
                                    <button onClick={onLogout} className="logout-btn">
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
            <main className="profile-main">
                <AnimatePresence mode="wait">
                    {activeTab === "dashboard" && (
                        <motion.div
                            key="dashboard"
                            className="dashboard-content"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                        >
                            <h1 className="page-title">Dashboard Overview</h1>

                            {/* Stats Grid */}
                            <div className="stats-grid">
                                <motion.div
                                    className="stat-card"
                                    whileHover={{ y: -5 }}
                                >
                                    <div className="stat-icon total">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                            <polyline points="14 2 14 8 20 8" />
                                        </svg>
                                    </div>
                                    <div className="stat-info">
                                        <p className="stat-label">Total Complaints</p>
                                        <h3 className="stat-value">{totalComplaints}</h3>
                                    </div>
                                </motion.div>

                                <motion.div
                                    className="stat-card"
                                    whileHover={{ y: -5 }}
                                >
                                    <div className="stat-icon pending">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <circle cx="12" cy="12" r="10" />
                                            <polyline points="12 6 12 12 16 14" />
                                        </svg>
                                    </div>
                                    <div className="stat-info">
                                        <p className="stat-label">Pending</p>
                                        <h3 className="stat-value">{pendingComplaints}</h3>
                                    </div>
                                </motion.div>

                                <motion.div
                                    className="stat-card"
                                    whileHover={{ y: -5 }}
                                >
                                    <div className="stat-icon resolved">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                            <polyline points="22 4 12 14.01 9 11.01" />
                                        </svg>
                                    </div>
                                    <div className="stat-info">
                                        <p className="stat-label">Resolved</p>
                                        <h3 className="stat-value">{resolvedComplaints}</h3>
                                    </div>
                                </motion.div>

                                <motion.div
                                    className="stat-card"
                                    whileHover={{ y: -5 }}
                                >
                                    <div className="stat-icon high-priority">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <circle cx="12" cy="12" r="10" />
                                            <line x1="12" y1="8" x2="12" y2="12" />
                                            <line x1="12" y1="16" x2="12.01" y2="16" />
                                        </svg>
                                    </div>
                                    <div className="stat-info">
                                        <p className="stat-label">High Priority</p>
                                        <h3 className="stat-value">{highPriorityCount}</h3>
                                    </div>
                                </motion.div>
                            </div>

                            {/* Category Stats - Migrated from old dashboard */}
                            <div className="category-stats-section">
                                <h2>Complaints by Category</h2>
                                <div className="category-grid">
                                    {Object.entries(categories).map(([name, count]) => (
                                        <div key={name} className="category-card">
                                            <span className="cat-name">{name}</span>
                                            <div className="cat-bar-container">
                                                <div
                                                    className="cat-bar-fill"
                                                    style={{ width: `${totalComplaints > 0 ? (count / totalComplaints) * 100 : 0}%` }}
                                                ></div>
                                            </div>
                                            <span className="cat-count">{count}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Quick Actions */}
                            <div className="quick-actions">
                                <h2>Quick Actions</h2>
                                <div className="action-buttons">
                                    <motion.button
                                        className="action-btn primary"
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => onNavigate("form")}
                                    >
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M12 5v14M5 12h14" />
                                        </svg>
                                        Submit New Complaint
                                    </motion.button>
                                    <motion.button
                                        className="action-btn delete"
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={handleDeleteUserComplaints}
                                        disabled={isDeleting}
                                        style={{ backgroundColor: showDeleteConfirm ? "rgba(239, 68, 68, 0.2)" : "transparent", color: "#ef4444", border: "1px solid rgba(239, 68, 68, 0.3)" }}
                                    >
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                        </svg>
                                        {showDeleteConfirm ? "Confirm Delete All?" : "Delete All Complaints"}
                                    </motion.button>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {activeTab === "profile" && (
                        <motion.div
                            key="profile"
                            className="profile-content"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                        >
                            <h1 className="page-title">My Profile</h1>

                            <div className="profile-card">
                                <div className="profile-header-section centered">
                                    <div className="profile-avatar-large">
                                        {user?.profile_image ? (
                                            <img src={user.profile_image} alt={user.full_name} />
                                        ) : (
                                            <div className="avatar-placeholder-large">
                                                {user?.full_name?.charAt(0).toUpperCase() || "U"}
                                            </div>
                                        )}
                                        <label className="image-update-label">
                                            <input type="file" accept="image/*" onChange={handleImageUpdate} style={{ display: 'none' }} />
                                            <div className="update-overlay">
                                                {updatingImage ? "..." : "📷"}
                                            </div>
                                        </label>
                                    </div>
                                    <div className="profile-header-info">
                                        <h2>{user?.full_name || "User"}</h2>
                                        <p className="user-role">{user?.role || "Strategic Member"}</p>
                                        <p className="user-email">{user?.email}</p>
                                        <div className="user-badges">
                                            <span className="badge">Active Member</span>
                                            <span className="badge">Verified</span>
                                            <span className="badge gold">Pro Agent</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="profile-bio-section">
                                    <p className="bio-text">{user?.bio || "No professional summary provided. Update your bio to tell others about your role in the AI grid."}</p>
                                </div>

                                {isEditingProfile ? (
                                    <form onSubmit={handleProfileUpdate} className="profile-edit-form">
                                        <div className="form-group">
                                            <label>Full Name</label>
                                            <input
                                                type="text"
                                                value={profileForm.full_name}
                                                onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Phone</label>
                                            <input
                                                type="text"
                                                value={profileForm.phone}
                                                onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Role</label>
                                            <input
                                                type="text"
                                                value={profileForm.role}
                                                onChange={(e) => setProfileForm({ ...profileForm, role: e.target.value })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Location</label>
                                            <input
                                                type="text"
                                                value={profileForm.location}
                                                onChange={(e) => setProfileForm({ ...profileForm, location: e.target.value })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Organization</label>
                                            <input
                                                type="text"
                                                value={profileForm.organization}
                                                onChange={(e) => setProfileForm({ ...profileForm, organization: e.target.value })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Bio / Summary</label>
                                            <textarea
                                                className="bio-input"
                                                value={profileForm.bio}
                                                onChange={(e) => setProfileForm({ ...profileForm, bio: e.target.value })}
                                                rows="3"
                                            ></textarea>
                                        </div>
                                        <div className="action-buttons centered">
                                            <button type="submit" className="action-btn primary">Save Changes</button>
                                            <button type="button" className="action-btn secondary" onClick={() => setIsEditingProfile(false)}>Cancel</button>
                                        </div>
                                    </form>
                                ) : (
                                    <div className="profile-details-section">
                                        <div className="profile-details">
                                            <div className="detail-row">
                                                <div className="detail-label">
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                                                        <polyline points="22,6 12,13 2,6" />
                                                    </svg>
                                                    Email
                                                </div>
                                                <div className="detail-value">{user?.email || "Not provided"}</div>
                                            </div>

                                            <div className="detail-row">
                                                <div className="detail-label">
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                                                    </svg>
                                                    Phone
                                                </div>
                                                <div className="detail-value">{user?.phone || "Not provided"}</div>
                                            </div>

                                            <div className="detail-row">
                                                <div className="detail-label">
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                                                        <line x1="9" y1="3" x2="9" y2="21" />
                                                    </svg>
                                                    Organization
                                                </div>
                                                <div className="detail-value">{user?.organization || "Not provided"}</div>
                                            </div>

                                            <div className="detail-row">
                                                <div className="detail-label">
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                                                        <circle cx="12" cy="10" r="3" />
                                                    </svg>
                                                    Location
                                                </div>
                                                <div className="detail-value">{user?.location || "Not provided"}</div>
                                            </div>

                                            <div className="detail-row">
                                                <div className="detail-label">
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                                                        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                                                    </svg>
                                                    Member Since
                                                </div>
                                                <div className="detail-value">
                                                    {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : "Recently Joined"}
                                                </div>
                                            </div>

                                            <div className="detail-row">
                                                <div className="detail-label">
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                                                    </svg>
                                                    Network Role
                                                </div>
                                                <div className="detail-value">{user?.role || "Strategic Member"}</div>
                                            </div>

                                            <div className="detail-row">
                                                <div className="detail-label">
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                                        <polyline points="22 4 12 14.01 9 11.01" />
                                                    </svg>
                                                    Resolution Score
                                                </div>
                                                <div className="detail-value">
                                                    {totalComplaints > 0 ? `${Math.round((resolvedComplaints / totalComplaints) * 100)}% Efficiency` : "N/A"}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="action-buttons centered mt-2">
                                            <button className="action-btn primary" onClick={() => setIsEditingProfile(true)}>Edit Profile</button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}

                    {activeTab === "complaints" && (
                        <motion.div
                            key="complaints"
                            className="complaints-content"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                        >
                            <h1 className="page-title">My Complaints</h1>

                            {complaints.length === 0 ? (
                                <div className="empty-state">
                                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                        <polyline points="14 2 14 8 20 8" />
                                    </svg>
                                    <h3>No complaints yet</h3>
                                    <p>Submit your first complaint to get started</p>
                                    <motion.button
                                        className="action-btn primary"
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => onNavigate("dashboard")}
                                    >
                                        Submit Complaint
                                    </motion.button>
                                </div>
                            ) : (
                                <div className="complaints-list">
                                    {complaints.map((complaint, index) => (
                                        <motion.div
                                            key={complaint.id}
                                            className="complaint-item"
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: index * 0.1 }}
                                        >
                                            <div className="complaint-header">
                                                <div className="complaint-id">{complaint.ticket_id || `#${complaint.id}`}</div>
                                                <div className="header-badges">
                                                    <span className={`priority-badge ${complaint.priority.toLowerCase()}`}>
                                                        {complaint.priority}
                                                    </span>
                                                    <span className={`category-badge ${complaint.category.toLowerCase()}`}>
                                                        {complaint.category}
                                                    </span>
                                                    <span className={`status-badge ${complaint.is_resolved ? 'resolved' : 'pending'}`}>
                                                        {complaint.is_resolved ? 'Resolved' : 'Pending'}
                                                    </span>
                                                </div>
                                            </div>
                                            <p className="complaint-text">{complaint.complaint_text}</p>
                                            <div className="complaint-footer">
                                                <span className="complaint-date">
                                                    {new Date(complaint.created_at).toLocaleDateString()}
                                                </span>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            )}
                        </motion.div>
                    )}

                    {activeTab === "feedback" && (
                        <motion.div
                            key="feedback"
                            className="feedback-tab-content"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                        >
                            <h1 className="page-title">Send Feedback</h1>

                            {feedbackSuccess ? (
                                <motion.div
                                    className="feedback-success-card centered-card"
                                    initial={{ scale: 0.9, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                >
                                    <div className="success-icon">✨</div>
                                    <h2>Thank you for your feedback!</h2>
                                    <p>Your input helps us improve the QuickFix AI grid for everyone.</p>
                                    <p className="redirect-note">Returning to dashboard...</p>
                                </motion.div>
                            ) : (
                                <div className="feedback-card centered-card">
                                    <p className="feedback-intro">We'd love to hear your thoughts on our AI-powered resolution system.</p>
                                    <form onSubmit={handleFeedbackSubmit} className="profile-feedback-form">
                                        <div className="form-group">
                                            <label>Experience Rating</label>
                                            <div className="rating-selector centered">
                                                {[1, 2, 3, 4, 5].map(num => (
                                                    <button
                                                        key={num}
                                                        type="button"
                                                        className={`rating-btn ${feedbackForm.rating === String(num) ? 'active' : ''}`}
                                                        onClick={() => setFeedbackForm({ ...feedbackForm, rating: String(num) })}
                                                    >
                                                        {num} ⭐
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="form-group">
                                            <label>How likely are you to recommend QuickFix AI?</label>
                                            <div className="nps-selector">
                                                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                                                    <button
                                                        key={num}
                                                        type="button"
                                                        className={`nps-btn ${feedbackForm.recommendation === String(num) ? 'active' : ''}`}
                                                        onClick={() => setFeedbackForm({ ...feedbackForm, recommendation: String(num) })}
                                                    >
                                                        {num}
                                                    </button>
                                                ))}
                                            </div>
                                            <div className="nps-labels">
                                                <span>Not Likely</span>
                                                <span>Highly Likely</span>
                                            </div>
                                        </div>

                                        <div className="form-group">
                                            <label>Your Detailed Thoughts</label>
                                            <textarea
                                                value={feedbackForm.message}
                                                onChange={(e) => setFeedbackForm({ ...feedbackForm, message: e.target.value })}
                                                placeholder="What specific areas should we focus on improving? We're listening..."
                                                rows="5"
                                                required
                                            ></textarea>
                                        </div>

                                        {feedbackError && <p className="error-message">{feedbackError}</p>}

                                        <motion.button
                                            type="submit"
                                            className="action-btn primary"
                                            disabled={feedbackLoading}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                        >
                                            {feedbackLoading ? "Transmitting..." : "Send Feedback →"}
                                        </motion.button>
                                    </form>
                                </div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>

            {/* Custom Delete Confirmation Modal */}
            <AnimatePresence>
                {showDeleteConfirm && (
                    <motion.div
                        className="modal-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <motion.div
                            className="confirm-modal"
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                        >
                            <div className="modal-icon warning">⚠️</div>
                            <h2>Delete All Complaints?</h2>
                            <p>This action cannot be undone. All your reported issues will be permanently removed from the AI grid.</p>
                            <div className="modal-actions">
                                <button
                                    className="action-btn delete"
                                    onClick={handleDeleteUserComplaints}
                                    disabled={isDeleting}
                                >
                                    {isDeleting ? "Deleting..." : "Confirm Delete"}
                                </button>
                                <button
                                    className="action-btn secondary"
                                    onClick={() => setShowDeleteConfirm(false)}
                                    disabled={isDeleting}
                                >
                                    Cancel
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div >
    );
}
