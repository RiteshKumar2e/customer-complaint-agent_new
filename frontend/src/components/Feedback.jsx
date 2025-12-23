import { useState } from "react";
import "../styles/Feedback.css";

export default function Feedback({ onClose }) {
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        rating: "5",
        category: "General",
        message: ""
    });
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState("");

    const categories = ["General", "Bug Report", "Feature Request", "UI/UX", "Performance", "Other"];
    const ratings = ["1", "2", "3", "4", "5"];

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
            // Create mailto link with feedback details
            const subject = `Quickfix Feedback - ${formData.category} (${formData.rating}⭐)`;
            const body = `
Name: ${formData.name}
Email: ${formData.email}
Rating: ${formData.rating}/5 ⭐
Category: ${formData.category}

Message:
${formData.message}

---
Sent from Quickfix Feedback System
      `.trim();

            const mailtoLink = `mailto:riteshkumar90359@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

            // Open email client
            window.location.href = mailtoLink;

            setSuccess(true);

            // Reset form after 2 seconds
            setTimeout(() => {
                setFormData({
                    name: "",
                    email: "",
                    rating: "5",
                    category: "General",
                    message: ""
                });
                setSuccess(false);
                if (onClose) onClose();
            }, 2000);

        } catch (err) {
            setError("Failed to send feedback. Please try again.");
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
                            <label htmlFor="rating">Rating *</label>
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
                            <label htmlFor="category">Category *</label>
                            <select
                                id="category"
                                name="category"
                                value={formData.category}
                                onChange={handleChange}
                                disabled={loading}
                            >
                                {categories.map(cat => (
                                    <option key={cat} value={cat}>{cat}</option>
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
