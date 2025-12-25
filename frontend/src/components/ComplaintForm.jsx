import { useState, useEffect } from "react";
import { submitComplaint, submitReview } from "../api";
import { showNotification } from "./NotificationCenter";
import "../styles/ComplaintForm.css";

export default function ComplaintForm({ onResult, user }) {
  const [formData, setFormData] = useState({
    name: user?.full_name || "",
    email: user?.email || "",
    category: "Technical",
    subject: "",
    description: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [steps, setSteps] = useState([]);
  const [showReview, setShowReview] = useState(false);
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [ticketId, setTicketId] = useState("");

  const categories = ["Technical", "Billing", "Delivery", "Service", "Security", "Other"];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError("");
  };

  const validateForm = () => {
    if (!formData.name.trim() || !formData.email.trim() || !formData.subject.trim() || !formData.description.trim()) {
      setError("All fields marked with * are required");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setError("");
    setSuccess(false);
    setShowReview(false);

    // Initial steps for visible solving
    setSteps([
      { name: "Initializing Multi-Agent Pipeline...", status: "active" },
      { name: "Scaling Resources for High Traffic...", status: "waiting" },
      { name: "AI Categorization & Priority Check...", status: "waiting" },
      { name: "Orchestrating Solution Strategy...", status: "waiting" },
      { name: "Finalizing Resolution Response...", status: "waiting" }
    ]);

    try {
      const updateStep = (idx) => {
        setSteps(prev => prev.map((s, i) =>
          i === idx ? { ...s, status: 'done' } :
            (i === idx + 1 ? { ...s, status: 'active' } : s)
        ));
      };

      // Progress simulation for transparency
      setTimeout(() => updateStep(0), 700);
      setTimeout(() => updateStep(1), 1500);
      setTimeout(() => updateStep(2), 2500);

      const res = await submitComplaint(formData.name, formData.email, formData.subject, formData.description);

      updateStep(3);
      updateStep(4);

      setTicketId(res.ticket_id);
      if (typeof onResult === "function") onResult(res);
      setSuccess(true);
      setShowReview(true);

      showNotification("success", "✅ Issue Resolved!", "AI agents completed the orchestration successfully.", "✨");

      setFormData({
        name: user?.full_name || "",
        email: user?.email || "",
        category: "Technical",
        subject: "",
        description: ""
      });
    } catch (err) {
      setError(err.response?.data?.detail || "System overload. Please try again.");
    } finally {
      setTimeout(() => setLoading(false), 800);
    }
  };

  const handleReview = async () => {
    if (rating === 0) {
      showNotification("error", "Rating Required", "Please select a star rating", "⚠️");
      return;
    }
    try {
      await submitReview(ticketId, rating, feedback);
      showNotification("success", "Feedback Received", "Thank you for reviewing our AI!", "⭐");
      setShowReview(false);
    } catch (e) {
      console.error(e);
      showNotification("error", "Error", "Failed to submit review.", "❌");
    }
  };

  return (
    <div className="complaint-form-container">
      {loading && (
        <div className="ai-processing-overlay">
          <div className="processing-card">
            <div className="processor-header">
              <span className="live-badge">LIVE ORCHESTRATION</span>
              <div className="ai-brain-pulse">🧠</div>
            </div>
            <h3>AI Solving Your Problem...</h3>
            <div className="steps-list">
              {steps.map((s, i) => (
                <div key={i} className={`step-row ${s.status}`}>
                  <div className="step-indicator">
                    {s.status === 'done' ? '✅' : (s.status === 'active' ? <div className="spinner-small"></div> : '○')}
                  </div>
                  <div className="step-text">{s.name}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="form-header">
        <h2>📝 AI Multi-Agent Portal</h2>
        <p>Enterprise-grade feedback system with high-concurrency support.</p>
      </div>

      <form className="complaint-form" onSubmit={handleSubmit}>
        <div className="form-section-wrapper">
          <div className="form-group">
            <label>Name</label>
            <input type="text" name="name" value={formData.name} onChange={handleChange} className="form-input" disabled={loading} />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" name="email" value={formData.email} onChange={handleChange} className="form-input" disabled={loading} />
          </div>
        </div>

        <div className="form-group">
          <label>Category</label>
          <select name="category" value={formData.category} onChange={handleChange} className="form-select" disabled={loading}>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label>Subject</label>
          <input type="text" name="subject" value={formData.subject} onChange={handleChange} className="form-input" placeholder="What's the issue?" disabled={loading} />
        </div>

        <div className="form-group">
          <label>Full Description</label>
          <textarea name="description" value={formData.description} onChange={handleChange} className="form-textarea" placeholder="Tell our AI agents exactly what happened..." rows="5" disabled={loading} />
        </div>

        {error && <div className="error-msg">{error}</div>}

        <button type="submit" className="launch-btn" disabled={loading}>
          {loading ? "Orchestrating AI..." : "🚀 Launch Multi-Agent Cluster"}
        </button>
      </form>

      {showReview && (
        <div className="review-block">
          <h3>⭐ Review AI Solution</h3>
          <p>Help us improve by rating the resolution for <strong>{ticketId}</strong></p>
          <div className="star-rating">
            {[1, 2, 3, 4, 5].map(s => (
              <button key={s} className={`star-btn ${rating >= s ? 'active' : ''}`} onClick={() => setRating(s)}>★</button>
            ))}
          </div>
          <textarea
            placeholder="How could our AI have handled this better?"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            className="review-textarea"
          />
          <button onClick={handleReview} className="submit-review-btn">Submit Feedback</button>
        </div>
      )}
    </div>
  );
}
