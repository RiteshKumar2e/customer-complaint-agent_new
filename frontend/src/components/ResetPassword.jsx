import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { resetPassword } from "../api";
import CustomCursor from "./CustomCursor";
import "../styles/Auth.css";

export default function ResetPassword({ onNavigate }) {
    const [token, setToken] = useState("");
    const [email, setEmail] = useState(""); // Optionally we can pass email or ask for it
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        // Extract token and email from URL
        const params = new URLSearchParams(window.location.search);
        const tokenParam = params.get("token");
        const emailParam = params.get("email");
        if (tokenParam) setToken(tokenParam);
        if (emailParam) setEmail(emailParam);
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (newPassword !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);
        setError("");

        try {
            await resetPassword(email, token, newPassword);
            setSuccess(true);
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to reset password.");
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="auth-container">
                <div className="auth-content">
                    <div className="auth-form-container" style={{ textAlign: 'center' }}>
                        <h2 className="auth-title">Success!</h2>
                        <p className="auth-subtitle">Your password has been reset successfully.</p>
                        <button className="auth-submit" onClick={() => onNavigate("login")}>Go to Login</button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <motion.div className="auth-container">
            <CustomCursor />
            <div className="auth-content">
                <motion.div className="auth-form-container">
                    <div className="auth-header">
                        <h2 className="auth-title">Create New Password</h2>
                        <p className="auth-subtitle">Please enter your email and your new password.</p>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Email Address</label>
                            <input
                                type="email"
                                placeholder="Verify your email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>

                        <div className="form-group">
                            <label>New Password</label>
                            <input
                                type="password"
                                placeholder="••••••••"
                                required
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                            />
                        </div>

                        <div className="form-group">
                            <label>Confirm Password</label>
                            <input
                                type="password"
                                placeholder="••••••••"
                                required
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                        </div>

                        {error && <div className="error-message" style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</div>}

                        <motion.button
                            type="submit"
                            className="auth-submit"
                            disabled={loading || !token}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            {loading ? "Resetting..." : "Reset Password"}
                        </motion.button>

                        {!token && <p style={{ color: '#ffcc00', marginTop: '10px', fontSize: '0.8rem' }}>Invalid or missing token in URL.</p>}
                    </form>
                </motion.div>
            </div>
        </motion.div>
    );
}
