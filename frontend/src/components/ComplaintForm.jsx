import { useState } from "react";
import { submitComplaint, submitReview, uploadAttachment, errorMessage } from "../api";
import { showNotification } from "../utils/notifications";
import "../styles/ComplaintForm.css";

export default function ComplaintForm({ onResult, user }) {
  const [formData, setFormData] = useState({
    name: user?.full_name || "",
    email: user?.email || "",
    subject: "",
    description: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [steps, setSteps] = useState([]);
  const [showReview, setShowReview] = useState(false);
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [ticketId, setTicketId] = useState("");
  const [files, setFiles] = useState([]);


  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError("");
  };

  const validateForm = () => {
    if (formData.subject.trim().length < 5) {
      setError("Subject must be at least 5 characters");
      return false;
    }
    if (formData.description.trim().length < 20) {
      setError("Please describe the problem in at least 20 characters");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setError("");
    setShowReview(false);

    setSteps([{ name: "Analysing your complaint (AI triage)…", status: "active" }]);

    try {
      const res = await submitComplaint(formData.subject.trim(), formData.description.trim());
      const uploadErrors = [];
      for (const file of files) {
        try {
          await uploadAttachment(res.ticket_id, file);
        } catch (uploadErr) {
          uploadErrors.push(`${file.name}: ${errorMessage(uploadErr)}`);
        }
      }
      setSteps((res.steps || []).map((step) => ({ name: `${step.step}: ${step.status}`, status: "done" })));
      setTicketId(res.ticket_id);
      if (typeof onResult === "function") onResult(res);
      setShowReview(true);
      showNotification("success", "Complaint submitted", `Ticket ${res.ticket_id} was created. We'll keep you updated.`, "✅");
      if (uploadErrors.length) setError(`Some attachments were not uploaded. ${uploadErrors.join(" ")}`);
      setFiles([]);
      setFormData({
        name: user?.full_name || "",
        email: user?.email || "",
        subject: "",
        description: ""
      });
    } catch (err) {
      setSteps([]);
      setError(errorMessage(err, "Could not submit your complaint. Please try again."));
    } finally {
      setTimeout(() => setLoading(false), 800);
    }
  };

  const handleReview = async () => {
    if (rating === 0) {
      showNotification("error", "Rating Required", "Please select a star rating", "⚠️");
      return;
    }
    // Feedback text is now optional
    try {
      await submitReview(ticketId, rating, feedback);
      showNotification("success", "Feedback Received", "Thank you for reviewing our AI!", "⭐");
      setShowReview(false);
      setRating(0);
      setFeedback("");
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
        <h2>Submit a complaint</h2>
        <p>Our AI sorts it by category and urgency; a support agent reviews anything sensitive before replying.</p>
      </div>

      <form className="complaint-form" onSubmit={handleSubmit}>
        <div className="form-section-wrapper">
          <div className="form-group">
            <label htmlFor="cf-name">Name (from your account)</label>
            <input id="cf-name" type="text" name="name" value={user?.full_name || ""} className="form-input" readOnly />
          </div>
          <div className="form-group">
            <label htmlFor="cf-email">Email (from your account)</label>
            <input id="cf-email" type="email" name="email" value={user?.email || ""} className="form-input" readOnly />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="cf-subject">Subject *</label>
          <input id="cf-subject" type="text" name="subject" maxLength={200} value={formData.subject} onChange={handleChange} className="form-input" placeholder="What's the issue?" disabled={loading} />
        </div>

        <div className="form-group">
          <label htmlFor="cf-desc">Full description * (at least 20 characters)</label>
          <textarea id="cf-desc" name="description" maxLength={5000} value={formData.description} onChange={handleChange} className="form-textarea" placeholder="Tell our AI agents exactly what happened..." rows="5" disabled={loading} />
        </div>

        <div className="form-group">
          <label htmlFor="cf-files">Attachments (optional: up to 3 PNG, JPEG, PDF or TXT files, 2 MB each)</label>
          <input id="cf-files" type="file" multiple accept=".png,.jpg,.jpeg,.pdf,.txt,image/png,image/jpeg,application/pdf,text/plain"
            disabled={loading}
            onChange={(e) => {
              const picked = Array.from(e.target.files || []);
              const tooBig = picked.find((f) => f.size > 2 * 1024 * 1024);
              if (picked.length > 3) setError("You can attach at most 3 files");
              else if (tooBig) setError(`${tooBig.name} is larger than 2 MB`);
              else { setError(""); setFiles(picked); }
            }} />
        </div>

        {error && <div className="error-msg" role="alert">{error}</div>}

        <button type="submit" className="launch-btn" disabled={loading}>
          {loading ? "Submitting…" : "Submit complaint"}
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
            placeholder="Additional feedback (optional) - How could our AI have handled this better?"
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
