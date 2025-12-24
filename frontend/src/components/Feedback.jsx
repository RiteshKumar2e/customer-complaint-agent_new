import { useState } from "react";
import { submitFeedback } from "../api";
import "../styles/Feedback.css";

export default function Feedback({ onClose }) {
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        rating: "5",
        recommendation: "8",
        message: ""
    });
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState("");

    const ratings = ["1", "2", "3", "4", "5"];
    const npsScores = Array.from({ length: 11 }, (_, i) => i.toString());

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        setError("");
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.name.trim() || !formData.email.trim() || !formData.message.trim()) {
            setError("Please fill in all required fields");
            return;
        }

        setLoading(true);
        setError("");

        try {
            // Send feedback to backend API
            const data = await submitFeedback({
                name: formData.name,
                email: formData.email,
                rating: parseInt(formData.rating),
                recommendation: parseInt(formData.recommendation),
                message: formData.message
            });

            setSuccess(true);

            // Reset form after 2 seconds
            setTimeout(() => {
                setFormData({
                    name: "",
                    email: "",
                    rating: "5",
                    recommendation: "8",
                    message: ""
                });
                setSuccess(false);
                if (onClose) onClose();
            }, 2000);

        } catch (err) {
            console.error("Feedback error:", err);
            let errorMessage = "Failed to send feedback. Please try again.";

            if (err.response?.status === 404) {
                errorMessage = "Backend server is not running. Please start the server.";
            } else if (err.code === 'ERR_NETWORK' || !err.response) {
                errorMessage = "Cannot connect to the server. Please make sure the backend is running.";
            } else if (err.response?.data?.detail) {
                if (Array.isArray(err.response.data.detail)) {
                    errorMessage = err.response.data.detail[0].msg;
                } else {
                    errorMessage = err.response.data.detail;
                }
            }

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="feedback-overlay" onClick={onClose}>
            <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
                <div className="feedback-header">
                    <h2>💬 Send Feedback</h2>
                    <button className="close-btn" onClick={onClose}>✕</button>
                </div>

                <form className="feedback-form" onSubmit={handleSubmit}>
                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="name">Name *</label>
                            <input
                                type="text"
                                id="name"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                placeholder="Your name"
                                disabled={loading}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="email">Email *</label>
                            <input
                                type="email"
                                id="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="your@email.com"
                                disabled={loading}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="rating">Overall Satisfaction *</label>
                            <select
                                id="rating"
                                name="rating"
                                value={formData.rating}
                                onChange={handleChange}
                                disabled={loading}
                            >
                                {ratings.map(r => (
                                    <option key={r} value={r}>{r} ⭐</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group">
                            <label htmlFor="recommendation">Likelihood to Recommend (0-10) *</label>
                            <select
                                id="recommendation"
                                name="recommendation"
                                value={formData.recommendation}
                                onChange={handleChange}
                                disabled={loading}
                            >
                                {npsScores.map(s => (
                                    <option key={s} value={s}>{s}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="message">Your Feedback *</label>
                        <textarea
                            id="message"
                            name="message"
                            value={formData.message}
                            onChange={handleChange}
                            placeholder="Tell us what you think..."
                            rows="5"
                            disabled={loading}
                            required
                        />
                    </div>

                    {error && <div className="alert alert-error">❌ {error}</div>}
                    {success && <div className="alert alert-success">✅ Feedback sent! Thank you!</div>}

                    <div className="form-actions">
                        <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
                            Cancel
                        </button>
                        <button type="submit" className="btn-primary" disabled={loading}>
                            {loading ? "Sending..." : "Send Feedback"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
