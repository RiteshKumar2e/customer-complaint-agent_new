import { useState, useEffect } from "react";
import {
  getAllComplaints,
  deleteAllComplaints
} from "../api";

import "../styles/Dashboard.css";

export default function Dashboard({ onNavigate, complaints = [], setComplaints }) {
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

  // Function to get estimated resolution time based on priority
  const getResolutionTime = (priority) => {
    switch(priority) {
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
        resolved: Math.floor(complaints.length * 0.6),
        avgSentiment: "Neutral"
      });

      setCategoryBreakdown(categories);
    }
  }, [complaints]);

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
      <nav className="dashboard-nav">
        <div className="nav-brand">
          <h1>📊 Complaint Dashboard</h1>
        </div>
        <div className="nav-buttons">
          <button className="nav-btn new-complaint" onClick={() => onNavigate("form")}>
            <span>➕</span> New Complaint
          </button>
          <button 
            className="nav-btn delete-all-btn" 
            onClick={handleDeleteAll}
            style={{
              backgroundColor: showDeleteConfirm ? "#ff4444" : "#ff6b6b",
              transition: "background-color 0.3s"
            }}
          >
            <span>🗑️</span> {showDeleteConfirm ? "Confirm Delete All?" : "Delete All"}
          </button>
          <button className="nav-btn back-home" onClick={() => {
            setShowDeleteConfirm(false);
            onNavigate("landing");
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
                  <div className="complaint-footer">
                    <span className="complaint-sentiment">😊 {complaint.sentiment}</span>
                    <span className="complaint-satisfaction">🎯 {complaint.satisfaction_prediction || complaint.satisfaction}</span>
                    <span className="complaint-resolution" style={{ marginLeft: "auto", color: "#0066cc", fontWeight: "bold" }}>
                      ⏱️ {getResolutionTime(complaint.priority)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
