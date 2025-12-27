import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { registerUser } from "../api";
import confetti from "canvas-confetti";
import "../styles/Auth.css";
import "../styles/AuthAnimations.css";

const CharacterEyes = ({ mousePos, containerRef, isHiding, isClosed, targetPos }) => {
    const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 });

    useEffect(() => {
        if (!containerRef.current || isHiding || isClosed) return;
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
    }, [mousePos, containerRef, isHiding, isClosed, targetPos]);

    return (
        <div className="char-eyes" style={{ opacity: isHiding ? 0 : 1, transition: '0.4s' }}>
            <div className="char-eye-socket" style={{
                height: isClosed ? '2px' : '14px',
                transition: 'height 0.3s ease'
            }}>
                <motion.div
                    className="char-pupil"
                    animate={{ x: isHiding || isClosed ? 0 : eyeOffset.x, y: isHiding || isClosed ? -5 : eyeOffset.y }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                    style={{ opacity: isClosed ? 0 : 1 }}
                />
            </div>
            <div className="char-eye-socket" style={{
                height: isClosed ? '2px' : '14px',
                transition: 'height 0.3s ease'
            }}>
                <motion.div
                    className="char-pupil"
                    animate={{ x: isHiding || isClosed ? 0 : eyeOffset.x, y: isHiding || isClosed ? -5 : eyeOffset.y }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                    style={{ opacity: isClosed ? 0 : 1 }}
                />
            </div>
        </div>
    );
};

const TermsModal = ({ isOpen, onClose, onAccept, initialTab = "terms" }) => {
    const [activeTab, setActiveTab] = useState(initialTab);

    useEffect(() => {
        if (isOpen) setActiveTab(initialTab);
    }, [isOpen, initialTab]);

    return (
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
                            <h3>Legal Agreement</h3>
                            <button className="close-modal" onClick={onClose}>&times;</button>
                        </div>

                        <div className="terms-modal-tabs">
                            <div
                                className={`terms-tab ${activeTab === "terms" ? "active" : ""}`}
                                onClick={() => setActiveTab("terms")}
                            >
                                Terms of Service
                            </div>
                            <div
                                className={`terms-tab ${activeTab === "privacy" ? "active" : ""}`}
                                onClick={() => setActiveTab("privacy")}
                            >
                                Privacy Policy
                            </div>
                        </div>

                        <div className="terms-modal-body">
                            {activeTab === "terms" ? (
                                <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
                                    <section>
                                        <h4>1. Acceptance of Terms</h4>
                                        <p>By creating an account on the Quickfix AI platform, you agree to abide by these Terms of Service. This platform is designed for legitimate complaint registration and resolution. Any misuse, including harassment or false reporting, will result in immediate account termination.</p>
                                    </section>
                                    <section>
                                        <h4>2. User Responsibilities</h4>
                                        <p>Users are responsible for maintaining the confidentiality of their account credentials. You agree to provide accurate, current, and complete information during the registration process.</p>
                                    </section>
                                    <section>
                                        <h4>3. AI Resolution Grid</h4>
                                        <p>Our autonomous sub-agents work around the clock to process your complaints. While we strive for extreme efficiency, the complexity of certain cases may require manual intervention from senior administrators.</p>
                                    </section>
                                    <section>
                                        <h4>4. Service Uptime</h4>
                                        <p>We maintain a 99.9% uptime for our decentralized neural nodes. Scheduled maintenance will be communicated 24 standard cycles in advance.</p>
                                    </section>
                                </motion.div>
                            ) : (
                                <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>
                                    <section>
                                        <h4>1. Data Collection</h4>
                                        <p>We collect essential identity data (name, email, phone) and organization details to facilitate the complaint resolution process. Profile pictures are stored securely to personalize your experience.</p>
                                    </section>
                                    <section>
                                        <h4>2. Neural Encryption</h4>
                                        <p>All communication within the Quickfix grid is encrypted using end-to-end neural protocols. Your personal information is never exposed to external non-authorized entities.</p>
                                    </section>
                                    <section>
                                        <h4>3. Use of AI</h4>
                                        <p>We use your complaint descriptions to train our local sub-agents for better pattern recognition. This data is anonymized before being fed into the central model.</p>
                                    </section>
                                    <section>
                                        <h4>4. Cookie Policy</h4>
                                        <p>Our system uses session tokens and essential state markers to maintain your connection to the grid. We do not use third-party tracking cookies for advertising.</p>
                                    </section>
                                </motion.div>
                            )}
                        </div>
                        <button className="modal-accept-btn" onClick={onAccept}>I Accept the Agreement</button>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default function Signup({ onNavigate }) {
    const [formData, setFormData] = useState({
        fullName: "", email: "", organization: "", phone: "", password: "", confirmPassword: "", profileImage: ""
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
    const [termsTab, setTermsTab] = useState("terms");
    const [isTyping, setIsTyping] = useState(false);
    const [activeField, setActiveField] = useState(null);
    const typingTimeoutRef = useRef(null);
    const [imagePreview, setImagePreview] = useState(null);

    useEffect(() => {
        const handleMove = (e) => setMousePos({ x: e.clientX, y: e.clientY });
        window.addEventListener("mousemove", handleMove);
        return () => window.removeEventListener("mousemove", handleMove);
    }, []);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setIsTyping(true);
        clearTimeout(typingTimeoutRef.current);
        typingTimeoutRef.current = setTimeout(() => setIsTyping(false), 500);
    };

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) { // 5MB limit
                setError("Image size should be less than 5MB");
                return;
            }
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result);
                setFormData({ ...formData, profileImage: reader.result });
            };
            reader.readAsDataURL(file);
        }
    };

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
            await registerUser(
                formData.email,
                formData.fullName,
                formData.password,
                formData.phone,
                formData.organization,
                formData.profileImage
            );
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

    const isHiding = isPasswordFocused && !showPassword; // Cover eyes with hands when typing password (hidden)
    const isClosed = showPassword && (formData.password.length > 0 || formData.confirmPassword.length > 0) && !isPasswordFocused; // Close eyes only when password is unhidden (visible)

    return (
        <motion.div className="auth-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <TermsModal
                isOpen={showTerms}
                initialTab={termsTab}
                onClose={() => setShowTerms(false)}
                onAccept={() => { setAgree(true); setShowTerms(false); }}
            />
            <div className="floating-glow glow-1" />
            <div className="floating-glow glow-2" />

            <div className="auth-illustration">
                <div className={`character-container ${isTyping ? 'typing' : ''}`} ref={illustrationRef}>
                    <motion.div
                        className={`char char-purple ${isHiding ? 'hiding-eyes' : ''}`}
                        animate={{
                            y: isTyping ? [0, -20, 0] : [0, -15, 0],
                            rotate: isTyping ? [0, 3, -3, 0] : 0
                        }}
                        transition={{
                            duration: isTyping ? 0.6 : 4,
                            repeat: Infinity,
                            ease: "easeInOut"
                        }}
                    >
                        <CharacterEyes mousePos={mousePos} containerRef={illustrationRef} isHiding={isHiding} isClosed={isClosed} targetPos={targetPos} />
                        <div className="char-hands"><div className="char-hand" /><div className="char-hand" /></div>
                    </motion.div>
                    <motion.div
                        className={`char char-orange ${isHiding ? 'hiding-eyes' : ''}`}
                        animate={{
                            scaleY: isTyping ? [1, 1.1, 1] : [1, 1.05, 1],
                            scaleX: isTyping ? [1, 0.95, 1] : 1
                        }}
                        transition={{
                            duration: isTyping ? 0.5 : 3,
                            repeat: Infinity,
                            ease: "easeInOut"
                        }}
                    >
                        <CharacterEyes mousePos={mousePos} containerRef={illustrationRef} isHiding={isHiding} isClosed={isClosed} targetPos={targetPos} />
                        <div className="char-hands"><div className="char-hand" /><div className="char-hand" /></div>
                    </motion.div>
                    <motion.div
                        className={`char char-black ${isHiding ? 'hiding-eyes' : ''}`}
                        animate={{
                            y: isTyping ? [0, -15, 0] : [0, -10, 0],
                            rotate: isTyping ? [0, -2, 2, 0] : 0
                        }}
                        transition={{
                            duration: isTyping ? 0.7 : 3.5,
                            repeat: Infinity,
                            ease: "easeInOut",
                            delay: 0.5
                        }}
                    >
                        <CharacterEyes mousePos={mousePos} containerRef={illustrationRef} isHiding={isHiding} isClosed={isClosed} targetPos={targetPos} />
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
                        {/* Profile Image Upload */}
                        <motion.div
                            className="profile-upload-section"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.2 }}
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                marginBottom: '1.5rem',
                                gap: '0.75rem'
                            }}
                        >
                            <input
                                type="file"
                                id="profileImage"
                                accept="image/*"
                                onChange={handleImageChange}
                                style={{ display: 'none' }}
                            />
                            <label
                                htmlFor="profileImage"
                                style={{
                                    cursor: 'pointer',
                                    position: 'relative'
                                }}
                            >
                                <motion.div
                                    className="profile-image-preview"
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    style={{
                                        width: '80px',
                                        height: '80px',
                                        borderRadius: '50%',
                                        background: imagePreview
                                            ? `url(${imagePreview}) center/cover`
                                            : 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(255, 138, 61, 0.2))',
                                        border: '3px solid rgba(139, 92, 246, 0.3)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        position: 'relative',
                                        overflow: 'hidden',
                                        boxShadow: '0 8px 24px rgba(139, 92, 246, 0.2)'
                                    }}
                                >
                                    {!imagePreview && (
                                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="rgba(139, 92, 246, 0.6)" strokeWidth="2">
                                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                            <circle cx="12" cy="7" r="4" />
                                        </svg>
                                    )}
                                    <div style={{
                                        position: 'absolute',
                                        bottom: 0,
                                        right: 0,
                                        background: 'linear-gradient(135deg, #10b981, #059669)',
                                        width: '28px',
                                        height: '28px',
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: '2px solid #050508',
                                        boxShadow: '0 4px 12px rgba(16, 185, 129, 0.4)'
                                    }}>
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                                            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                                            <circle cx="12" cy="13" r="4" />
                                        </svg>
                                    </div>
                                </motion.div>
                            </label>
                            <p style={{
                                fontSize: '0.8rem',
                                color: 'var(--text-tertiary)',
                                textAlign: 'center',
                                marginTop: '-0.25rem'
                            }}>
                                {imagePreview ? 'Click to change' : 'Upload Identity Photo'}
                            </p>
                        </motion.div>

                        <div className="form-grid">
                            <div className="form-group">
                                <label>Full Name</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                                    <input name="fullName" placeholder="Enter your name" required value={formData.fullName} onFocus={updateTargetPos} onBlur={() => setTargetPos(null)} onChange={handleChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Phone Number</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
                                    <input name="phone" placeholder="+91 00000 00000" required value={formData.phone} onFocus={updateTargetPos} onBlur={() => setTargetPos(null)} onChange={handleChange} />
                                </div>
                            </div>
                            <div className="form-group full-width">
                                <label>Email Address</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
                                    <input name="email" type="email" placeholder="email@domain.com" required value={formData.email} onFocus={updateTargetPos} onBlur={() => setTargetPos(null)} onChange={handleChange} />
                                </div>
                            </div>
                            <div className="form-group full-width">
                                <label>Organization</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="9" y1="3" x2="9" y2="21" /></svg>
                                    <input name="organization" placeholder="Org/Company" required value={formData.organization} onFocus={updateTargetPos} onBlur={() => setTargetPos(null)} onChange={handleChange} />
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
                            <span>
                                I have read and agree to the
                                <span className="auth-link" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setTermsTab("terms"); setShowTerms(true); }}>Terms of Service</span>
                                and
                                <span className="auth-link" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setTermsTab("privacy"); setShowTerms(true); }}>Privacy Policy</span>.
                            </span>
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
