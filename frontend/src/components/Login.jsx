import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GoogleOAuthProvider, useGoogleLogin } from "@react-oauth/google";
import { googleAuth, googleVerifyOTP } from "../api";
import CustomCursor from "./CustomCursor";
import OTPModal from "./OTPModal";
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

export default function Login({ onNavigate, onLoginSuccess }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [rememberMe, setRememberMe] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
    const [targetPos, setTargetPos] = useState(null);
    const [isPasswordFocused, setIsPasswordFocused] = useState(false);
    const [showOTPModal, setShowOTPModal] = useState(false);
    const [otpEmail, setOtpEmail] = useState("");
    const [otpLoading, setOtpLoading] = useState(false);
    const illustrationRef = useRef(null);
    const emailRef = useRef(null);
    const passwordRef = useRef(null);

    // Load saved credentials on mount
    useEffect(() => {
        const savedCreds = localStorage.getItem("saved_creds");
        if (savedCreds) {
            try {
                const { email: savedEmail, password: savedPassword } = JSON.parse(savedCreds);
                setEmail(savedEmail);
                setPassword(savedPassword);
                setRememberMe(true);
            } catch (e) {
                console.error("Failed to parse saved credentials");
            }
        }
    }, []);

    useEffect(() => {
        const handleMove = (e) => setMousePos({ x: e.clientX, y: e.clientY });
        window.addEventListener("mousemove", handleMove);
        return () => window.removeEventListener("mousemove", handleMove);
    }, []);

    const updateTargetPos = (ref) => {
        if (ref.current) {
            const rect = ref.current.getBoundingClientRect();
            setTargetPos({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 });
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        // Handle Remember Me logic
        if (rememberMe) {
            localStorage.setItem("saved_creds", JSON.stringify({ email, password }));
        } else {
            localStorage.removeItem("saved_creds");
        }

        setTimeout(() => {
            onLoginSuccess({ email, name: email.split('@')[0] });
            setLoading(false);
        }, 1500);
    };

    const handleGoogleLogin = useGoogleLogin({
        onSuccess: async (tokenResponse) => {
            setLoading(true);
            setError("");
            try {
                // Fetch user info from Google
                const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                    headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
                });
                const userInfo = await userInfoResponse.json();

                // Send email to backend to trigger OTP
                const response = await googleAuth(userInfo.email, userInfo.name);

                if (response.requires_otp) {
                    setOtpEmail(userInfo.email);
                    setShowOTPModal(true);
                } else {
                    // Fallback if OTP not required
                    onLoginSuccess(response.user);
                }
            } catch (err) {
                setError(err.response?.data?.detail || "Google sign-in failed");
            } finally {
                setLoading(false);
            }
        },
        onError: () => {
            setError("Google sign-in was cancelled or failed");
        },
    });

    const handleOTPVerify = async (otp) => {
        setOtpLoading(true);
        try {
            const response = await googleVerifyOTP(otpEmail, otp);
            localStorage.setItem("token", response.access_token);
            localStorage.setItem("user", JSON.stringify(response.user));
            onLoginSuccess(response.user);
            setShowOTPModal(false);
        } catch (err) {
            throw err; // Let OTPModal handle the error display
        } finally {
            setOtpLoading(false);
        }
    };

    const isHiding = isPasswordFocused && !showPassword;

    return (
        <motion.div
            className="auth-container"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            <CustomCursor />

            {/* Background Animations */}
            <div className="floating-glow glow-1" />
            <div className="floating-glow glow-2" />

            <div className="auth-particles">
                {[...Array(15)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="auth-particle"
                        style={{ width: '4px', height: '4px', left: `${Math.random() * 100}%`, top: `${Math.random() * 100}%` }}
                        animate={{ y: [0, -40, 0], opacity: [0.1, 0.3, 0.1] }}
                        transition={{ duration: Math.random() * 5 + 5, repeat: Infinity }}
                    />
                ))}
            </div>

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
                <motion.div className="back-link" onClick={() => onNavigate("landing")} whileHover={{ x: -10 }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M19 12H5M12 19l-7-7 7-7" /></svg>
                    Back to home
                </motion.div>

                <motion.div
                    className="auth-form-container"
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                >
                    <div className="auth-header">
                        <motion.div
                            className="auth-brand-icon"
                            whileHover={{ rotate: 10, scale: 1.1 }}
                        >
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                        </motion.div>
                        <h2 className="auth-title">Welcome Back</h2>
                        <p className="auth-subtitle">Log in to your profile</p>
                    </div>

                    <form className="auth-form" onSubmit={handleLogin}>
                        <div className="form-group">
                            <label>Email Address</label>
                            <div className="input-wrapper">
                                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
                                <input
                                    ref={emailRef}
                                    type="email"
                                    placeholder="Enter your email"
                                    required
                                    onFocus={() => updateTargetPos(emailRef)}
                                    onBlur={() => setTargetPos(null)}
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <label>Password</label>
                                <span className="auth-link" style={{ fontSize: '0.85rem' }} onClick={() => onNavigate("forgot-password")}>Forgot Access?</span>
                            </div>
                            <div className="input-wrapper">
                                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                                <input
                                    ref={passwordRef}
                                    type={showPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    required
                                    onFocus={() => { setIsPasswordFocused(true); updateTargetPos(passwordRef); }}
                                    onBlur={() => { setIsPasswordFocused(false); setTargetPos(null); }}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                                <div className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                                    {showPassword ? "🙈" : "👁️"}
                                </div>
                            </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '-0.5rem' }}>
                            <label className="terms-row" style={{ margin: 0 }}>
                                <input
                                    type="checkbox"
                                    checked={rememberMe}
                                    onChange={(e) => setRememberMe(e.target.checked)}
                                />
                                <span>Remember Me</span>
                            </label>
                        </div>

                        <motion.button
                            type="submit"
                            className="auth-submit"
                            disabled={loading}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            {loading ? "Authenticating..." : "Login"}
                        </motion.button>

                        <div className="divider">OR CONNECT VIA</div>

                        <motion.button
                            type="button"
                            className="google-btn"
                            onClick={handleGoogleLogin}
                            whileHover={{ backgroundColor: "rgba(255,255,255,0.08)" }}
                        >
                            <svg width="20" height="20" viewBox="0 0 48 48">
                                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
                                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
                                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
                                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
                                <path fill="none" d="M0 0h48v48H0z" />
                            </svg>
                            Sync with Google
                        </motion.button>
                    </form>

                    <div className="auth-footer">
                        Don't have an account? <span className="auth-link" onClick={() => onNavigate("signup")}>Signup</span>
                    </div>
                </motion.div>
            </div>

            {/* OTP Modal for Google Sign-In */}
            <OTPModal
                isOpen={showOTPModal}
                onClose={() => setShowOTPModal(false)}
                email={otpEmail}
                onVerify={handleOTPVerify}
                loading={otpLoading}
            />
        </motion.div>
    );
}
