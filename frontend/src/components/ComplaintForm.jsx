import { useState } from "react";
import { submitComplaint } from "../api";
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

  const categories = ["Technical", "Billing", "Delivery", "Service", "Security", "Other"];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError("");
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError("Name is required");
      return false;
    }
    if (!formData.email.trim()) {
      setError("Email is required");
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError("Please enter a valid email address");
      return false;
    }
    if (!formData.subject.trim()) {
      setError("Subject is required");
      return false;
    }
    if (!formData.description.trim()) {
      setError("Description is required");
      return false;
    }
    if (formData.description.trim().length < 10) {
      setError("Description must be at least 10 characters");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      // Combine subject and description for the complaint text
      const complaintText = `[${formData.category}] ${formData.subject}\n\n${formData.description}`;

      const res = await submitComplaint(formData.name, formData.email, complaintText);

      if (typeof onResult === "function") {
        onResult(res);
      }

      setSuccess(true);

      // Show success notification with agent's solution
      showNotification(
        "success",
        "✅ Problem Solved!",
        `Your ${formData.category} complaint has been analyzed and resolved. Solution: ${res.solution || "Check the details below"} - Check your email for full details.`,
        "✨"
      );

      // Also request browser notification permission and show notification
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("Quickfix - Problem Solved!", {
          body: `Your complaint has been resolved...`,
          // Remove the 'icon' line if you don't have an image file
          tag: "complaint-resolved",
          requireInteraction: false,
        });
      } else if ("Notification" in window && Notification.permission !== "denied") {
        Notification.requestPermission().then((permission) => {
          if (permission === "granted") {
            new Notification("Quickfix - Problem Solved!", {
              body: `Your complaint has been resolved by our AI agents. Check your email for details.`,
            });
          }
        });
      }

      setFormData({
        name: user?.full_name || "",
        email: user?.email || "",
        category: "Technical",
        subject: "",
        description: ""
      });

      // Clear success message after 5 seconds  
      setTimeout(() => setSuccess(false), 5000);
    } catch (err) {
      console.error("Submission error:", err);
      let errorMessage = "Failed to submit complaint. Please try again.";

      if (err.response?.status === 404) {
        errorMessage = "Backend server is not running. Please start the server.";
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        errorMessage = "Cannot connect to the server. Please make sure the backend is running on port 8000.";
      } else {
        errorMessage = err.response?.data?.detail || errorMessage;
      }

      setError(errorMessage);

      // Show error notification
      showNotification(
        "error",
        "❌ Error",
        errorMessage,
        "⚠️"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="complaint-form-container">
      <div className="form-header">
        <h2>📝 Submit Your Complaint</h2>
        <p>We're here to help. Please provide us with detailed information about your issue.</p>
      </div>

      <form className="complaint-form" onSubmit={handleSubmit}>
        {/* Personal Information Section */}
        <fieldset className="form-section">
          <legend>Personal Information</legend>

          <div className="form-group">
            <label htmlFor="name">Full Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter your full name"
              readOnly={!!user}
              className={`form-input ${user ? 'readonly-input' : ''}`}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="your.email@example.com"
              readOnly={!!user}
              className={`form-input ${user ? 'readonly-input' : ''}`}
              disabled={loading}
            />
          </div>
        </fieldset>

        {/* Complaint Details Section */}
        <fieldset className="form-section">
          <legend>Complaint Details</legend>

          <div className="form-group">
            <label htmlFor="category">Category *</label>
            <select
              id="category"
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="form-select"
              disabled={loading}
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="subject">Subject *</label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              placeholder="Brief summary of your issue"
              className="form-input"
              maxLength="100"
              disabled={loading}
            />
            <small className="char-count">{formData.subject.length}/100</small>
          </div>

          <div className="form-group full-width">
            <label htmlFor="description">
              Description *
              <span className="required-hint">Minimum 10 characters</span>
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Please provide detailed information about your complaint. The more details you provide, the better we can assist you."
              className="form-textarea"
              rows="6"
              disabled={loading}
            />
            <small className="char-count">{formData.description.length} characters</small>
          </div>
        </fieldset>

        {/* Error/Success Messages */}
        {error && <div className="alert alert-error">❌ {error}</div>}
        {success && <div className="alert alert-success">✅ Complaint submitted successfully! Our AI agents are processing your request.</div>}

        {/* Submit Button */}
        <div className="form-actions">
          <button
            type="submit"
            className="submit-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Submitting...
              </>
            ) : (
              <>
                <span>🚀</span>
                Submit Complaint
              </>
            )}
          </button>
          <p className="form-note">* Required fields</p>
        </div>
      </form>
    </div>
  );
}
