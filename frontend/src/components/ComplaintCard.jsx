import { useState } from "react";
import { motion } from "framer-motion";
import "../styles/ComplaintCard.css";

export default function ComplaintCard({ data }) {
  const [showSolution, setShowSolution] = useState(false);
  const getPriorityColor = (priority) => {
    switch (priority) {
      case "High": return "#ff6b6b";
      case "Medium": return "#ffd93d";
      case "Low": return "#22c55e";
      default: return "#94a3b8";
    }
  };

  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case "Angry": return "😠";
      case "Negative": return "😞";
      case "Neutral": return "😐";
      case "Positive": return "😊";
      default: return "😐";
    }
  };

  const getSatisfactionColor = (satisfaction) => {
    switch (satisfaction) {
      case "High": return "#22c55e";
      case "Medium": return "#ffd93d";
      case "Low": return "#ff6b6b";
      default: return "#94a3b8";
    }
  };

  return (
    <div className="complaint-card-container">
      <div className="card-header">
        <div className="ticket-badge">
          {data.ticket_id || "NEW TICKET"}
        </div>
        <h2> AI Analysis Complete</h2>
        <p>Here's what our 6 AI agents found:</p>
      </div>

      <div className="cards-grid">
        {/* Category Card */}
        <div className="info-card category-card">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <label>Category</label>
            <p>{data.category}</p>
          </div>
        </div>

        {/* Priority Card */}
        <div className="info-card priority-card" style={{ borderLeftColor: getPriorityColor(data.priority) }}>
          <div className="card-icon">⚡</div>
          <div className="card-content">
            <label>Priority</label>
            <p style={{ color: getPriorityColor(data.priority) }}>{data.priority}</p>
          </div>
        </div>

        {/* Sentiment Card */}
        <div className="info-card sentiment-card">
          <div className="card-icon">{getSentimentIcon(data.sentiment)}</div>
          <div className="card-content">
            <label>Sentiment</label>
            <p>{data.sentiment}</p>
          </div>
        </div>

        {/* Satisfaction Card */}
        <div className="info-card satisfaction-card" style={{ borderLeftColor: getSatisfactionColor(data.satisfaction || data.satisfaction_prediction) }}>
          <div className="card-icon">🎯</div>
          <div className="card-content">
            <label>Expected Satisfaction</label>
            <p style={{ color: getSatisfactionColor(data.satisfaction || data.satisfaction_prediction) }}>{data.satisfaction || data.satisfaction_prediction}</p>
          </div>
        </div>
      </div>

      {/* Subject & Description Section */}
      <div className="content-section">
        <div className="section-title">
          <span>📝</span>
          Complaint Details
        </div>
        <div className="subject-line">
          <strong>Subject:</strong> {data.subject || "No Subject"}
        </div>
        <p className="description-text">
          {data.description || data.complaint_text}
        </p>
      </div>

      {/* Full Response Section */}
      <div className="response-section">
        <div className="section-title">
          <span>💬</span>
          Recommended Response
        </div>
        <p className="response-text">{data.response}</p>
      </div>

      {/* Solution Section */}
      <div className="solution-section">
        <div
          className="section-title"
          onClick={() => setShowSolution(!showSolution)}
          style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>💡</span>
            Suggested Solution
          </div>
          <button className="view-solution-btn">
            {showSolution ? "Hide Solution" : "View Solution"}
          </button>
        </div>
        {showSolution && (
          <motion.div
            className="solution-content"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            transition={{ duration: 0.3 }}
          >
            <p className="solution-text">{data.solution}</p>

            {(data.ai_analysis_steps || data.steps) && (
              <div className="steps-container" style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', opacity: 0.8 }}>Actionable Steps:</h4>
                <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
                  {(typeof (data.ai_analysis_steps || data.steps) === 'string'
                    ? JSON.parse(data.ai_analysis_steps || data.steps)
                    : (data.ai_analysis_steps || data.steps)).map((step, idx) => (
                      <li key={idx} style={{ fontSize: '0.85rem', marginBottom: '0.4rem', opacity: 0.9 }}>{step}</li>
                    ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Action Section */}
      <div className="action-section">
        <div className="section-title">
          <span>🎬</span>
          Recommended Action
        </div>
        <div className="action-badge">{data.action}</div>
      </div>

      {/* Similar Issues Section */}
      {(data.similar_issues || data.similar_complaints) && (
        <div className="similar-section">
          <div className="section-title">
            <span>🔍</span>
            Similar Issues Found
          </div>
          <p className="similar-text">{data.similar_issues || data.similar_complaints}</p>
        </div>
      )}
    </div>
  );
}
