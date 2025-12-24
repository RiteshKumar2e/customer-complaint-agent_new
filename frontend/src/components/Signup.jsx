import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { registerUser } from "../api";
import confetti from "canvas-confetti";
import "../styles/Auth.css";

const CharacterEyes = ({ mousePos, containerRef, isHiding, targetPos }) => {
    const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 });

    useEffect(() => {
        if (!containerRef.current || isHiding) return;
        const rect = containerRef.current.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        let deltaX, deltaY;
        if (targetPos) {
            deltaX = targetPos.x - centerX;
            deltaY = targetPos.y - centerY;
        } else {
            deltaX = mousePos.x - centerX;
            deltaY = mousePos.y - centerY;
        }

        const angle = Math.atan2(deltaY, deltaX);
        const distance = Math.min(6, Math.sqrt(deltaX ** 2 + deltaY ** 2) / 20);

        setEyeOffset({
            x: Math.cos(angle) * distance,
            y: Math.sin(angle) * distance
        });
    }, [mousePos, containerRef, isHiding, targetPos]);

    return (
        <div className="char-eyes" style={{ opacity: isHiding ? 0 : 1, transition: '0.4s' }}>
            <div className="char-eye-socket">
                <motion.div
                    className="char-pupil"
                    animate={{ x: isHiding ? 0 : eyeOffset.x, y: isHiding ? -5 : eyeOffset.y }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                />
            </div>
            <div className="char-eye-socket">
                <motion.div
                    className="char-pupil"
                    animate={{ x: isHiding ? 0 : eyeOffset.x, y: isHiding ? -5 : eyeOffset.y }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                />
            </div>
        </div>
    );
};

const TermsModal = ({ isOpen, onClose, onAccept }) => (
    <AnimatePresence>
        {isOpen && (
            <motion.div
                className="terms-modal-overlay"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
            >
                <motion.div
                    className="terms-modal-content"
                    initial={{ scale: 0.9, y: 20 }}
                    animate={{ scale: 1, y: 0 }}
                    exit={{ scale: 0.9, y: 20 }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="terms-modal-header">
                        <h3>Terms & Privacy Policy</h3>
                        <button className="close-modal" onClick={onClose}>&times;</button>
                    </div>
                    <div className="terms-modal-body">
                        <section>
                            <h4>1. Terms of Service</h4>
                            <p>By accessing this AI-powered complaint platform, you agree to provide accurate information and NOT use the service for malicious reporting or harassment. We reserve the right to terminate accounts that violate our community guidelines.</p>
                        </section>
                        <section>
                            <h4>2. Data Privacy</h4>
                            <p>Your data is encrypted using neural-grade protocols. We do not sell your personal information to third parties. We use your complaint data only to improve the resolution process and train our local sub-agents for better efficiency.</p>
                        </section>
                        <section>
                            <h4>3. Responsiveness</h4>
                            <p>While our agents are highly efficient, response times may vary based on system load. We strive for a 99.9% uptime for our AI resolution grid.</p>
                        </section>
                        <section>
                            <h4>4. Cookie Policy</h4>
                            <p>We use essential session tokens to keep your neural link active. No tracking cookies are used for advertising purposes.</p>
                        </section>
                    </div>
                    <button className="modal-accept-btn" onClick={onAccept}>I Understand & Accept</button>
                </motion.div>
            </motion.div>
        )}
    </AnimatePresence>
);

export default function Signup({ onNavigate }) {
    const [formData, setFormData] = useState({
        fullName: "", email: "", organization: "", phone: "", password: "", confirmPassword: ""
    });
    const [showPassword, setShowPassword] = useState(false);
    const [agree, setAgree] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
    const [targetPos, setTargetPos] = useState(null);
    const [isPasswordFocused, setIsPasswordFocused] = useState(false);
    const illustrationRef = useRef(null);
    const [showTerms, setShowTerms] = useState(false);

    useEffect(() => {
        const handleMove = (e) => setMousePos({ x: e.clientX, y: e.clientY });
        window.addEventListener("mousemove", handleMove);
        return () => window.removeEventListener("mousemove", handleMove);
    }, []);

    const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

    const updateTargetPos = (e) => {
        const rect = e.target.getBoundingClientRect();
        setTargetPos({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 });
    };

    const handleSignup = async (e) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) return setError("Passwords do not match");
        if (!agree) return setError("Agree to Terms first");

        setLoading(true);
        setError("");
        try {
            await registerUser(formData.email, formData.fullName);
            setSuccess(true);
            confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#8b5cf6', '#ffffff', '#ff8a3d']
            });
            setTimeout(() => onNavigate("login"), 2500);
        } catch (err) { setError("Registration failed. Email might exist."); }
        finally { setLoading(false); }
    };

    const isHiding = isPasswordFocused && !showPassword;

    return (
        <motion.div className="auth-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <TermsModal
                isOpen={showTerms}
                onClose={() => setShowTerms(false)}
                onAccept={() => { setAgree(true); setShowTerms(false); }}
            />
            <div className="floating-glow glow-1" />
            <div className="floating-glow glow-2" />

            <div className="auth-illustration">
                <div className="character-container" ref={illustrationRef}>
                    <motion.div className={`char char-purple ${isHiding ? 'hiding-eyes' : ''}`} animate={{ y: [0, -15, 0] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}>
                        <CharacterEyes mousePos={mousePos} containerRef={illustrationRef} isHiding={isHiding} targetPos={targetPos} />
                        <div className="char-hands"><div className="char-hand" /><div className="char-hand" /></div>
                    </motion.div>
                    <motion.div className={`char char-orange ${isHiding ? 'hiding-eyes' : ''}`} animate={{ scaleY: [1, 1.05, 1] }} transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}>
                        <CharacterEyes mousePos={mousePos} containerRef={illustrationRef} isHiding={isHiding} targetPos={targetPos} />
                        <div className="char-hands"><div className="char-hand" /><div className="char-hand" /></div>
                    </motion.div>
                    <motion.div className={`char char-black ${isHiding ? 'hiding-eyes' : ''}`} animate={{ y: [0, -10, 0] }} transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}>
                        <CharacterEyes mousePos={mousePos} containerRef={illustrationRef} isHiding={isHiding} targetPos={targetPos} />
                        <div className="char-hands"><div className="char-hand" /><div className="char-hand" /></div>
                    </motion.div>
                </div>
            </div>

            <div className="auth-content">
                <div className="back-link" onClick={() => onNavigate("landing")}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M19 12H5M12 19l-7-7 7-7" /></svg> Back to home</div>

                <motion.div className="auth-form-container" initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} transition={{ type: "spring", stiffness: 100, damping: 20 }}>
                    <div className="auth-header">
                        <div className="auth-brand-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg></div>
                        <h2 className="auth-title">Create Your Account</h2>
                        <p className="auth-subtitle">Join us in the decentralized AI grid</p>
                    </div>

                    {error && <div style={{ color: "#ef4444", textAlign: 'center', marginBottom: "1rem" }}>{error}</div>}
                    {success && <div style={{ color: "#22c55e", textAlign: 'center', marginBottom: "1rem" }}>Account Established! Syncing...</div>}

                    <form className="auth-form" onSubmit={handleSignup}>
                        <div className="form-grid">
                            <div className="form-group">
                                <label>Identity Name</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                                    <input name="fullName" placeholder="Full Name" required value={formData.fullName} onFocus={updateTargetPos} onBlur={() => setTargetPos(null)} onChange={handleChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Email Address</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
                                    <input name="email" type="email" placeholder="email@domain.com" required value={formData.email} onFocus={updateTargetPos} onBlur={() => setTargetPos(null)} onChange={handleChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Organization</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="9" y1="3" x2="9" y2="21" /></svg>
                                    <input name="organization" placeholder="Org/Company" required value={formData.organization} onFocus={updateTargetPos} onBlur={() => setTargetPos(null)} onChange={handleChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Link Number</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
                                    <input name="phone" placeholder="+91 xxxxxxxxx" required value={formData.phone} onFocus={updateTargetPos} onBlur={() => setTargetPos(null)} onChange={handleChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Password</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                                    <input name="password" type={showPassword ? "text" : "password"} placeholder="••••••" required onFocus={(e) => { setIsPasswordFocused(true); updateTargetPos(e); }} onBlur={() => { setIsPasswordFocused(false); setTargetPos(null); }} value={formData.password} onChange={handleChange} />
                                    <div className="password-toggle" onClick={() => setShowPassword(!showPassword)}>{showPassword ? "🙈" : "👁️"}</div>
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Confirm Password</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                                    <input name="confirmPassword" type={showPassword ? "text" : "password"} placeholder="••••••" required onFocus={(e) => { setIsPasswordFocused(true); updateTargetPos(e); }} onBlur={() => { setIsPasswordFocused(false); setTargetPos(null); }} value={formData.confirmPassword} onChange={handleChange} />
                                </div>
                            </div>
                        </div>

                        <label className="terms-row">
                            <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
                            <span>Agree to <span className="auth-link" onClick={() => setShowTerms(true)}>Terms of Service</span> and <span className="auth-link" onClick={() => setShowTerms(true)}>Privacy Policy</span>.</span>
                        </label>

                        <motion.button type="submit" className="auth-submit" disabled={loading || success} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                            {loading ? "Establishing..." : "Create Account →"}
                        </motion.button>
                    </form>
                    <div className="auth-footer">Already have an account? <span className="auth-link" onClick={() => onNavigate("login")}>Sign in</span></div>
                </motion.div>
            </div>
        </motion.div>
    );
}
