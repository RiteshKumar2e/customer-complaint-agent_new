import { useState, useEffect } from "react";
import {
  getAllComplaints,
  deleteAllComplaints,
  submitResolutionFeedback
} from "../api";

import "../styles/Dashboard.css";

export default function Dashboard({ onNavigate, onLogout, user, complaints = [], setComplaints }) {
  const [stats, setStats] = useState({
    total: 0,
    highPriority: 0,
    resolved: 0,
    avgSentiment: "Neutral"
  });

  const [categoryBreakdown, setCategoryBreakdown] = useState({
    Billing: 0,
    Technical: 0,
    Delivery: 0,
    Service: 0,
    Security: 0,
    Other: 0
  });

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // Resolution feedback states
  const [showResolutionFeedback, setShowResolutionFeedback] = useState(false);
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [resolutionFeedbackLoading, setResolutionFeedbackLoading] = useState(false);
  const [resolutionComment, setResolutionComment] = useState("");
  const [expandedSolutions, setExpandedSolutions] = useState({});

  const toggleSolution = (id) => {
    setExpandedSolutions(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // Function to get estimated resolution time based on priority
  const getResolutionTime = (priority) => {
    switch (priority) {
      case "High":
        return "24-48 hours";
      case "Medium":
        return "3-5 days";
      case "Low":
        return "7-10 days";
      default:
        return "5-7 days";
    }
  };

  useEffect(() => {
    if (complaints.length > 0) {
      const highCount = complaints.filter(c => c.priority === "High").length;
      const resolvedCount = complaints.filter(c => c.is_resolved).length;
      const categories = { Billing: 0, Technical: 0, Delivery: 0, Service: 0, Security: 0, Other: 0 };

      complaints.forEach(c => {
        if (categories.hasOwnProperty(c.category)) {
          categories[c.category]++;
        } else {
          categories.Other++;
        }
      });

      setStats({
        total: complaints.length,
        highPriority: highCount,
        resolved: resolvedCount,
        avgSentiment: "Neutral"
      });

      setCategoryBreakdown(categories);
    }
  }, [complaints]);

  const handleResolutionFeedback = async (isResolved) => {
    if (!selectedComplaint) return;

    setResolutionFeedbackLoading(true);
    try {
      await submitResolutionFeedback(
        selectedComplaint.ticket_id,
        isResolved,
        resolutionComment
      );

      // Update local state if needed (though usually we refresh from parent)
      // If setComplaints is available, we could update it
      if (setComplaints) {
        setComplaints(prev => prev.map(c =>
          c.ticket_id === selectedComplaint.ticket_id ? { ...c, user_resolution_feedback: isResolved, user_resolution_comment: resolutionComment } : c
        ));
      }

      // Close modal and reset
      setShowResolutionFeedback(false);
      setSelectedComplaint(null);
      setResolutionComment("");

      alert(isResolved
        ? "Thank you! We're glad your issue was resolved."
        : "Thank you for your feedback. Our admin team has been notified."
      );
    } catch (error) {
      console.error("Resolution feedback error:", error);
      alert("Failed to submit feedback. Please try again.");
    } finally {
      setResolutionFeedbackLoading(false);
    }
  };

  const handleDeleteAll = async () => {
    if (!showDeleteConfirm) {
      setShowDeleteConfirm(true);
      return;
    }

    try {
      await deleteAllComplaints();
      setComplaints([]);
      setShowDeleteConfirm(false);
      alert("✅ All complaints have been deleted successfully!");
    } catch (error) {
      console.error("Error deleting complaints:", error);
      alert("❌ Failed to delete complaints. Please try again.");
    }
  };

  return (
    <div className="dashboard-container">
      {/* Navigation */}
      <nav className={`dashboard-nav ${isMenuOpen ? 'menu-open' : ''}`}>
        <div className="nav-brand">
          <h1>📊 Complaint Dashboard</h1>
        </div>

        <button className="dashboard-menu-toggle" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          <span className={`hamburger ${isMenuOpen ? 'active' : ''}`}></span>
        </button>

        <div className={`nav-buttons ${isMenuOpen ? 'is-open' : ''}`}>
          {user && (
            <div className="user-info-chip">
              <span className="user-avatar">
                {user.full_name?.charAt(0) || 'U'}
              </span>
              <span className="user-name">{user.full_name || user.email}</span>
            </div>
          )}
          <button className="nav-btn new-complaint" onClick={() => { onNavigate("form"); setIsMenuOpen(false); }}>
            <span>➕</span> New Complaint
          </button>
          <button
            className="nav-btn delete-all-btn"
            onClick={handleDeleteAll}
            style={{
              backgroundColor: showDeleteConfirm ? "#ff4444" : "#ff6b6b"
            }}
          >
            <span>🗑️</span> {showDeleteConfirm ? "Confirm Delete All?" : "Delete All"}
          </button>
          <button className="nav-btn logout-btn" onClick={() => { onLogout(); setIsMenuOpen(false); }}>
            <span>🚪</span> Logout
          </button>
          <button className="nav-btn back-home" onClick={() => {
            setShowDeleteConfirm(false);
            onNavigate("landing");
            setIsMenuOpen(false);
          }}>
            <span>🏠</span> Home
          </button>
        </div>
      </nav>

      <div className="dashboard-content">
        {/* Stats Grid */}
        <div className="stats-grid fade-in">
          <div className="stat-card stat-total">
            <div className="stat-icon">📋</div>
            <div className="stat-info">
              <p className="stat-label">Total Complaints</p>
              <h3 className="stat-value">{stats.total}</h3>
            </div>
            <div className="stat-trend">All-time</div>
          </div>

          <div className="stat-card stat-urgent">
            <div className="stat-icon">🚨</div>
            <div className="stat-info">
              <p className="stat-label">High Priority</p>
              <h3 className="stat-value">{stats.highPriority}</h3>
            </div>
            <div className="stat-trend">Urgent</div>
          </div>

          <div className="stat-card stat-resolved">
            <div className="stat-icon">✅</div>
            <div className="stat-info">
              <p className="stat-label">Resolved</p>
              <h3 className="stat-value">{stats.resolved}</h3>
            </div>
            <div className="stat-trend">Completed</div>
          </div>

          <div className="stat-card stat-sentiment">
            <div className="stat-icon">😊</div>
            <div className="stat-info">
              <p className="stat-label">Avg Sentiment</p>
              <h3 className="stat-value" style={{ fontSize: "18px" }}>
                {stats.avgSentiment}
              </h3>
            </div>
            <div className="stat-trend">Overall</div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="charts-section">
          {/* Category Breakdown */}
          <div className="chart-card fade-in" style={{ animationDelay: "0.1s" }}>
            <h2 className="chart-title">📂 Complaints by Category</h2>
            <div className="category-breakdown">
              {Object.entries(categoryBreakdown).map(([category, count]) => (
                <div key={category} className="category-row">
                  <div className="category-info">
                    <span className="category-name">{category}</span>
                    <span className="category-count">{count}</span>
                  </div>
                  <div className="category-bar">
                    <div
                      className="category-fill"
                      style={{
                        width: `${stats.total > 0 ? (count / stats.total) * 100 : 0}%`,
                        animation: `slideRight 0.8s ease-out ${0.1 + Object.keys(categoryBreakdown).indexOf(category) * 0.05}s forwards`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Priority Distribution */}
          <div className="chart-card fade-in" style={{ animationDelay: "0.2s" }}>
            <h2 className="chart-title">⚡ Priority Distribution</h2>
            <div className="priority-grid">
              <div className="priority-item high">
                <div className="priority-circle">
                  <span>{complaints.filter(c => c.priority === "High").length}</span>
                </div>
                <p>High</p>
              </div>
              <div className="priority-item medium">
                <div className="priority-circle">
                  <span>{complaints.filter(c => c.priority === "Medium").length}</span>
                </div>
                <p>Medium</p>
              </div>
              <div className="priority-item low">
                <div className="priority-circle">
                  <span>{complaints.filter(c => c.priority === "Low").length}</span>
                </div>
                <p>Low</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Complaints */}
        <div className="recent-section fade-in" style={{ animationDelay: "0.3s" }}>
          <h2 className="section-title">📝 Recent Complaints</h2>
          {complaints.length === 0 ? (
            <div className="empty-state">
              <p>📭 No complaints yet</p>
              <button className="empty-cta" onClick={() => onNavigate("form")}>
                Submit Your First Complaint
              </button>
            </div>
          ) : (
            <div className="complaints-list">
              {complaints.slice(-5).reverse().map((complaint, idx) => (
                <div key={idx} className="complaint-item">
                  <div className="complaint-header">
                    <span className="complaint-category">📂 {complaint.category}</span>
                    <span className={`complaint-priority priority-${complaint.priority.toLowerCase()}`}>
                      {complaint.priority} Priority
                    </span>
                  </div>
                  <p className="complaint-text">{(complaint.complaint_text || complaint.text || "").substring(0, 100)}...</p>

                  {complaint.solution && (
                    <div className="solution-preview-container" style={{ marginTop: '8px' }}>
                      <button
                        onClick={() => toggleSolution(complaint.id || complaint.ticket_id)}
                        style={{
                          background: 'rgba(16, 185, 129, 0.1)',
                          color: '#10b981',
                          border: '1px solid #10b981',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '10px',
                          fontWeight: '600',
                          cursor: 'pointer',
                          display: 'block',
                          marginBottom: expandedSolutions[complaint.id || complaint.ticket_id] ? '4px' : '0'
                        }}
                      >
                        {expandedSolutions[complaint.id || complaint.ticket_id] ? "Hide Solution ▲" : "View Solution ▼"}
                      </button>
                      {expandedSolutions[complaint.id || complaint.ticket_id] && (
                        <div className="solution-preview" style={{
                          padding: '8px',
                          background: 'rgba(16, 185, 129, 0.1)',
                          borderLeft: '3px solid #10b981',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}>
                          <strong style={{ color: '#10b981' }}>Solution:</strong> {complaint.solution}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="complaint-footer">
                    <span className="complaint-sentiment">😊 {complaint.sentiment}</span>
                    <span className="complaint-satisfaction">🎯 {complaint.satisfaction_prediction || complaint.satisfaction}</span>

                    <button
                      className="resolve-btn-dashboard"
                      onClick={() => {
                        setSelectedComplaint(complaint);
                        setShowResolutionFeedback(true);
                      }}
                      style={{
                        marginLeft: "auto",
                        padding: "6px 12px",
                        borderRadius: "8px",
                        border: "none",
                        color: "white",
                        background: complaint.user_resolution_feedback === true
                          ? "linear-gradient(135deg, #10b981, #059669)"
                          : complaint.user_resolution_feedback === false
                            ? "linear-gradient(135deg, #f59e0b, #d97706)"
                            : "linear-gradient(135deg, #6366f1, #4f46e5)",
                        cursor: "pointer",
                        fontSize: "12px",
                        fontWeight: "600",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
                        transition: "all 0.3s ease"
                      }}
                    >
                      {complaint.user_resolution_feedback === true ? "✅ Resolved" :
                        complaint.user_resolution_feedback === false ? "❌ Not Resolved" :
                          "❓ Confirm Resolution"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Resolution Feedback Modal */}
      {showResolutionFeedback && selectedComplaint && (
        <div className="dashboard-modal-overlay">
          <div className="dashboard-modal">
            <h3>Was Your Issue Resolved?</h3>
            <p className="modal-subtitle">Ticket #{selectedComplaint.ticket_id}</p>

            <div className="feedback-form">
              <textarea
                value={resolutionComment}
                onChange={(e) => setResolutionComment(e.target.value)}
                placeholder="Any additional comments? (Optional)"
                rows="3"
                className="modal-textarea"
              />

              <div className="modal-actions">
                <button
                  className="modal-btn success"
                  onClick={() => handleResolutionFeedback(true)}
                  disabled={resolutionFeedbackLoading}
                >
                  {resolutionFeedbackLoading ? "..." : "Yes, Resolved"}
                </button>
                <button
                  className="modal-btn warning"
                  onClick={() => handleResolutionFeedback(false)}
                  disabled={resolutionFeedbackLoading}
                >
                  {resolutionFeedbackLoading ? "..." : "No, Not Resolved"}
                </button>
                <button
                  className="modal-btn secondary"
                  onClick={() => {
                    setShowResolutionFeedback(false);
                    setSelectedComplaint(null);
                    setResolutionComment("");
                  }}
                  disabled={resolutionFeedbackLoading}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
