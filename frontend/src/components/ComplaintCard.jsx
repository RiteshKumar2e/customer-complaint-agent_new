import "../styles/ComplaintCard.css";

export default function ComplaintCard({ data }) {
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
        <div className="section-title">
          <span>💡</span>
          Suggested Solution
        </div>
        <p className="solution-text">{data.solution}</p>
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
