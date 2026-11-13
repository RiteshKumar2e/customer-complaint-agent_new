import { useState } from "react";
import { motion } from "framer-motion";
import { forgotPassword, resetPassword, errorMessage } from "../api";
import { validateEmail, validatePassword } from "../utils/validation";
import "../styles/Auth.css";
import Logo from "./Logo";

const RESEND_SECONDS = 60;

/** Password reset by email OTP: request a code, then enter it with a new password. */
export default function ForgotPassword({ onNavigate }) {
    const [step, setStep] = useState("email");
    const [email, setEmail] = useState("");
    const [code, setCode] = useState("");
    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [resendAt, setResendAt] = useState(0);

    const requestCode = async (e) => {
        e?.preventDefault();
        const problem = validateEmail(email);
        if (problem) return setError(problem);
        setLoading(true);
        setError("");
        try {
            const data = await forgotPassword(email.trim().toLowerCase());
            setMessage(data.message);
            setStep("code");
            setResendAt(Date.now() + RESEND_SECONDS * 1000);
        } catch (err) {
            setError(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    const submitReset = async (e) => {
        e.preventDefault();
        const problem = (!/^\d{6}$/.test(code) && "Enter the 6-digit code from your email") ||
            validatePassword(password) || (password !== confirm && "Passwords do not match");
        if (problem) return setError(problem);
        setLoading(true);
        setError("");
        try {
            const data = await resetPassword(email.trim().toLowerCase(), code, password);
            setMessage(data.message);
            setStep("done");
        } catch (err) {
            setError(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    const canResend = Date.now() >= resendAt;

    return (
        <motion.div className="auth-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="auth-content">
                <motion.button type="button" className="back-link" onClick={() => onNavigate("login")} whileHover={{ x: -10 }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true"><path d="M19 12H5M12 19l-7-7 7-7" /></svg>
                    Back to Login
                </motion.button>

                <motion.div className="auth-form-container" initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                    <div className="auth-header">
                        <div className="auth-logo"><Logo height={40} /></div>
                        <h2 className="auth-title">{step === "done" ? "Password updated" : "Reset your password"}</h2>
                        <p className="auth-subtitle">
                            {step === "email" && "Enter your account email. We'll send a 6-digit code that is valid for 5 minutes."}
                            {step === "code" && `Enter the code sent to ${email.trim().toLowerCase()} and choose a new password.`}
                            {step === "done" && "All other sessions were signed out."}
                        </p>
                    </div>

                    {message && step !== "email" && (
                        <div className="success-message" role="status">{message}</div>
                    )}

                    {step === "email" && (
                        <form className="auth-form" onSubmit={requestCode} noValidate>
                            <div className="form-group">
                                <label htmlFor="fp-email">Email address</label>
                                <div className="input-wrapper">
                                    <input id="fp-email" type="email" autoComplete="email" placeholder="you@example.com" required
                                        value={email} onChange={(e) => setEmail(e.target.value)} />
                                </div>
                            </div>
                            {error && <div className="error-message" role="alert">{error}</div>}
                            <button type="submit" className="auth-submit" disabled={loading}>{loading ? "Sending..." : "Send code"}</button>
                        </form>
                    )}

                    {step === "code" && (
                        <form className="auth-form" onSubmit={submitReset} noValidate>
                            <div className="form-group">
                                <label htmlFor="fp-code">6-digit code</label>
                                <div className="input-wrapper">
                                    <input id="fp-code" inputMode="numeric" autoComplete="one-time-code" maxLength={6} required
                                        value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label htmlFor="fp-pass">New password</label>
                                <div className="input-wrapper">
                                    <input id="fp-pass" type="password" autoComplete="new-password" required
                                        value={password} onChange={(e) => setPassword(e.target.value)} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label htmlFor="fp-confirm">Confirm new password</label>
                                <div className="input-wrapper">
                                    <input id="fp-confirm" type="password" autoComplete="new-password" required
                                        value={confirm} onChange={(e) => setConfirm(e.target.value)} />
                                </div>
                            </div>
                            {error && <div className="error-message" role="alert">{error}</div>}
                            <button type="submit" className="auth-submit" disabled={loading}>{loading ? "Saving..." : "Reset password"}</button>
                            <button type="button" className="auth-link-button" disabled={!canResend || loading} onClick={requestCode}>
                                {canResend ? "Send a new code" : "You can request a new code in a minute"}
                            </button>
                        </form>
                    )}

                    {step === "done" && (
                        <button type="button" className="auth-submit" onClick={() => onNavigate("login")}>Go to login</button>
                    )}
                </motion.div>
            </div>
        </motion.div>
    );
}
