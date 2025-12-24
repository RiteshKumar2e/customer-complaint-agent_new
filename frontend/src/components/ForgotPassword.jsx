import { useState } from "react";
import { motion } from "framer-motion";
import { forgotPassword } from "../api";
import CustomCursor from "./CustomCursor";
import "../styles/Auth.css";

export default function ForgotPassword({ onNavigate }) {
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setMessage("");

        try {
            const data = await forgotPassword(email);
            setMessage(data.message);
        } catch (err) {
            setError(err.response?.data?.detail || "Something went wrong. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            className="auth-container"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            <CustomCursor />
            <div className="auth-content">
                <motion.div className="back-link" onClick={() => onNavigate("login")} whileHover={{ x: -10 }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M19 12H5M12 19l-7-7 7-7" /></svg>
                    Back to Login
                </motion.div>

                <motion.div
                    className="auth-form-container"
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                >
                    <div className="auth-header">
                        <div className="auth-brand-icon">🔑</div>
                        <h2 className="auth-title">Forgot Password?</h2>
                        <p className="auth-subtitle">Enter your email and we'll send you a link to reset your password.</p>
                    </div>

                    {message ? (
                        <div className="success-message" style={{ color: '#10b981', background: 'rgba(16, 185, 129, 0.1)', padding: '1rem', borderRadius: '10px', marginBottom: '1.5rem', textAlign: 'center' }}>
                            {message}
                        </div>
                    ) : (
                        <form className="auth-form" onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label>Email Address</label>
                                <div className="input-wrapper">
                                    <input
                                        type="email"
                                        placeholder="Enter your email"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                    />
                                </div>
                            </div>

                            {error && <div className="error-message" style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</div>}

                            <motion.button
                                type="submit"
                                className="auth-submit"
                                disabled={loading}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {loading ? "Sending..." : "Send Reset Link"}
                            </motion.button>
                        </form>
                    )}
                </motion.div>
            </div>
        </motion.div>
    );
}
