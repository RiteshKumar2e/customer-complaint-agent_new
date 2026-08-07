import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "../styles/OTPModal.css";

const OTP_LENGTH = 6;
const EMPTY_OTP = Array(OTP_LENGTH).fill("");

// Each box drifts in from its own direction and snaps into the row,
// so the group settles instead of just fading in.
const SCATTER = [
    { x: -64, y: -48, rotate: -18 },
    { x: 30, y: -72, rotate: 13 },
    { x: -26, y: 58, rotate: 10 },
    { x: 68, y: 44, rotate: -15 },
    { x: -58, y: 26, rotate: 17 },
    { x: 44, y: -34, rotate: -9 },
];

// Success copy resolves out of a blur instead of just appearing
const BLUR_IN = {
    hidden: { opacity: 0, y: 12, filter: "blur(14px)" },
    visible: (delay = 0) => ({
        opacity: 1,
        y: 0,
        filter: "blur(0px)",
        transition: { duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] },
    }),
};

const RESEND_COOLDOWN = 30;

export default function OTPModal({ isOpen, onClose, email, onVerify, onVerified, onResend, loading }) {
    const [otp, setOtp] = useState(EMPTY_OTP);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    // idle -> verifying -> success | error
    const [status, setStatus] = useState("idle");
    const [cooldown, setCooldown] = useState(RESEND_COOLDOWN);
    const [resending, setResending] = useState(false);
    // Bumped on every resend so the boxes remount and replay their entry
    const [round, setRound] = useState(0);
    const inputsRef = useRef([]);
    const submittingRef = useRef(false);
    const timersRef = useRef([]);

    const addTimer = (id) => timersRef.current.push(id);
    const clearTimers = () => {
        timersRef.current.forEach(clearTimeout);
        timersRef.current = [];
    };

    useEffect(() => {
        if (!isOpen) return;
        setOtp(EMPTY_OTP);
        setError("");
        setNotice("");
        setStatus("idle");
        setResending(false);
        setRound(0);
        // A code was just sent, so the cooldown starts full
        setCooldown(RESEND_COOLDOWN);
        submittingRef.current = false;
        // Focus first input once the boxes have started settling
        const id = setTimeout(() => inputsRef.current[0]?.focus(), 260);
        addTimer(id);
        return clearTimers;
    }, [isOpen]);

    // Resend countdown - one timeout per tick, so the deps stay simple
    useEffect(() => {
        if (!isOpen || cooldown <= 0) return;
        const id = setTimeout(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
        return () => clearTimeout(id);
    }, [isOpen, cooldown]);

    useEffect(() => clearTimers, []);

    const focusInput = (index) => inputsRef.current[index]?.focus();

    const submitOtp = useCallback(async (value) => {
        if (submittingRef.current) return;
        submittingRef.current = true;
        setError("");
        setStatus("verifying");

        try {
            await onVerify(value);
            setStatus("success");
            // Hold the success state long enough to be read, then hand back
            addTimer(setTimeout(() => (onVerified || onClose)(), 2200));
        } catch (err) {
            setStatus("error");
            setError(err.response?.data?.detail || "Invalid OTP. Please try again.");
            // Shake, then reset the boxes so the user can retype
            addTimer(setTimeout(() => {
                setOtp(EMPTY_OTP);
                setStatus("idle");
                submittingRef.current = false;
                focusInput(0);
            }, 700));
        }
    }, [onVerify, onVerified, onClose]);

    const handleResend = async () => {
        if (!onResend || resending || cooldown > 0 || status !== "idle") return;

        setResending(true);
        setError("");
        setNotice("");
        try {
            await onResend();
            setOtp(EMPTY_OTP);
            submittingRef.current = false;
            setRound((r) => r + 1);
            setCooldown(RESEND_COOLDOWN);
            setNotice("A new code is on its way to your inbox.");
            addTimer(setTimeout(() => setNotice(""), 4000));
            addTimer(setTimeout(() => focusInput(0), 260));
        } catch (err) {
            setError(err.response?.data?.detail || "Couldn't resend the code. Try again.");
        } finally {
            setResending(false);
        }
    };

    const commitOtp = (nextOtp) => {
        setOtp(nextOtp);
        const joined = nextOtp.join("");
        // Auto-verify as soon as all six digits are in
        if (joined.length === OTP_LENGTH) {
            addTimer(setTimeout(() => submitOtp(joined), 180));
        }
    };

    const handleChange = (index, value) => {
        if (status !== "idle") return;
        if (value.length > 1) return;
        if (!/^\d*$/.test(value)) return;

        const newOtp = [...otp];
        newOtp[index] = value;
        if (error) setError("");
        commitOtp(newOtp);

        if (value && index < OTP_LENGTH - 1) focusInput(index + 1);
    };

    const handleKeyDown = (index, e) => {
        if (status !== "idle") return;

        if (e.key === "Backspace" && !otp[index] && index > 0) {
            focusInput(index - 1);
        } else if (e.key === "ArrowLeft" && index > 0) {
            e.preventDefault();
            focusInput(index - 1);
        } else if (e.key === "ArrowRight" && index < OTP_LENGTH - 1) {
            e.preventDefault();
            focusInput(index + 1);
        }
    };

    const handlePaste = (e) => {
        e.preventDefault();
        if (status !== "idle") return;

        const pastedData = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, OTP_LENGTH);
        if (!pastedData) return;

        const newOtp = [...EMPTY_OTP];
        for (let i = 0; i < pastedData.length; i++) newOtp[i] = pastedData[i];
        if (error) setError("");
        commitOtp(newOtp);

        focusInput(Math.min(pastedData.length, OTP_LENGTH - 1));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const otpValue = otp.join("");
        if (otpValue.length !== OTP_LENGTH) {
            setError("Please enter all 6 digits");
            return;
        }
        submitOtp(otpValue);
    };

    if (!isOpen) return null;

    const isBusy = status === "verifying" || status === "success" || loading;
    const filledCount = otp.filter(Boolean).length;

    return (
        <motion.div
            className="otp-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={status === "idle" ? onClose : undefined}
        >
            <motion.div
                className={`otp-modal-content otp-status-${status}`}
                initial={{ scale: 0.92, opacity: 0, y: 24 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.94, opacity: 0, y: 16 }}
                transition={{ type: "spring", stiffness: 340, damping: 26 }}
                onClick={(e) => e.stopPropagation()}
            >
                <AnimatePresence mode="wait">
                    {status === "success" ? (
                        <motion.div
                            key="success"
                            className="otp-success"
                            initial={{ opacity: 0, scale: 0.94 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.28, ease: "easeOut" }}
                        >
                            <motion.h2
                                className="otp-success-title"
                                variants={BLUR_IN}
                                initial="hidden"
                                animate="visible"
                                custom={0}
                            >
                                Verified successfully
                            </motion.h2>
                            <motion.p
                                className="otp-success-sub"
                                variants={BLUR_IN}
                                initial="hidden"
                                animate="visible"
                                custom={0.14}
                            >
                                Your email has been verified.
                            </motion.p>

                            <div className="otp-success-stage">
                                <svg className="otp-orbit" viewBox="0 0 200 200" aria-hidden="true">
                                    <defs>
                                        <linearGradient id="otpArcGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                            <stop offset="0%" stopColor="#22c55e" stopOpacity="0" />
                                            <stop offset="55%" stopColor="#22c55e" stopOpacity="0.85" />
                                            <stop offset="100%" stopColor="#86efac" stopOpacity="1" />
                                        </linearGradient>
                                    </defs>

                                    {/* Track draws itself once the check lands */}
                                    <motion.circle
                                        cx="100" cy="100" r="82"
                                        fill="none"
                                        stroke="rgba(34, 197, 94, 0.16)"
                                        strokeWidth="1.5"
                                        initial={{ pathLength: 0, opacity: 0 }}
                                        animate={{ pathLength: 1, opacity: 1 }}
                                        transition={{ duration: 0.9, ease: "easeOut", delay: 0.15 }}
                                    />

                                    {/* Bright arc sweeping clockwise */}
                                    <motion.g
                                        className="otp-orbit-spin"
                                        initial={{ rotate: 0 }}
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 2.6, repeat: Infinity, ease: "linear" }}
                                    >
                                        <circle
                                            className="otp-orbit-arc"
                                            cx="100" cy="100" r="82"
                                            fill="none"
                                            stroke="url(#otpArcGradient)"
                                            strokeWidth="2.5"
                                            strokeLinecap="round"
                                            strokeDasharray="150 365"
                                        />
                                    </motion.g>

                                    {/* Dotted inner ring drifting the other way */}
                                    <motion.g
                                        className="otp-orbit-spin"
                                        initial={{ rotate: 0 }}
                                        animate={{ rotate: -360 }}
                                        transition={{ duration: 7, repeat: Infinity, ease: "linear" }}
                                    >
                                        <circle
                                            cx="100" cy="100" r="64"
                                            fill="none"
                                            stroke="rgba(34, 197, 94, 0.5)"
                                            strokeWidth="1.5"
                                            strokeLinecap="round"
                                            strokeDasharray="2 12"
                                        />
                                    </motion.g>
                                </svg>

                                {/* Single shockwave on arrival */}
                                <motion.span
                                    className="otp-success-ring"
                                    initial={{ scale: 0.3, opacity: 0.6 }}
                                    animate={{ scale: 1.3, opacity: 0 }}
                                    transition={{ duration: 1.1, ease: "easeOut", delay: 0.1 }}
                                />

                                <motion.div
                                    className="otp-success-badge"
                                    initial={{ scale: 0.4, opacity: 0, rotate: -12 }}
                                    animate={{ scale: 1, opacity: 1, rotate: 0 }}
                                    transition={{ type: "spring", stiffness: 420, damping: 18, delay: 0.08 }}
                                >
                                    <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
                                        <motion.path
                                            d="M5 12.5L10 17.5L19 7.5"
                                            stroke="currentColor"
                                            strokeWidth="2.6"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            initial={{ pathLength: 0 }}
                                            animate={{ pathLength: 1 }}
                                            transition={{ duration: 0.42, delay: 0.22, ease: "easeOut" }}
                                        />
                                    </svg>
                                </motion.div>
                            </div>

                            <motion.p
                                className="otp-success-tag"
                                variants={BLUR_IN}
                                initial="hidden"
                                animate="visible"
                                custom={0.62}
                            >
                                Verified &amp; Secured 🔒
                            </motion.p>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="form"
                            initial={{ opacity: 1 }}
                            exit={{ opacity: 0, scale: 0.97 }}
                            transition={{ duration: 0.18 }}
                        >
                            <div className="otp-modal-header">
                                <motion.div
                                    className="otp-icon"
                                    initial={{ scale: 0.6, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    transition={{ type: "spring", stiffness: 420, damping: 20 }}
                                >
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                                        <polyline points="22,6 12,13 2,6" />
                                    </svg>
                                </motion.div>
                                <h2>Let's verify your email</h2>
                                <p>We've sent a 6-digit code to</p>
                                <p className="otp-email">{email}</p>
                                <p className="otp-hint">It'll auto-verify once entered.</p>
                            </div>

                            <form onSubmit={handleSubmit} className="otp-form">
                                <motion.div
                                    className="otp-inputs"
                                    animate={status === "error" ? { x: [0, -11, 9, -7, 5, 0] } : { x: 0 }}
                                    transition={{ duration: 0.42 }}
                                >
                                    {otp.map((digit, index) => (
                                        <motion.div
                                            key={`${round}-${index}`}
                                            className={`otp-box ${digit ? "filled" : ""} ${status === "error" ? "invalid" : ""}`}
                                            initial={{ ...SCATTER[index], opacity: 0, scale: 0.7 }}
                                            animate={{ x: 0, y: 0, rotate: 0, opacity: 1, scale: 1 }}
                                            transition={{
                                                type: "spring",
                                                stiffness: 300,
                                                damping: 20,
                                                delay: 0.05 + index * 0.06,
                                            }}
                                        >
                                            <input
                                                ref={(el) => {
                                                    inputsRef.current[index] = el;
                                                }}
                                                id={`otp-${index}`}
                                                type="text"
                                                inputMode="numeric"
                                                autoComplete={index === 0 ? "one-time-code" : "off"}
                                                maxLength="1"
                                                value={digit}
                                                disabled={isBusy}
                                                onChange={(e) => handleChange(index, e.target.value)}
                                                onKeyDown={(e) => handleKeyDown(index, e)}
                                                onPaste={handlePaste}
                                                className="otp-input"
                                            />
                                            <AnimatePresence>
                                                {digit && (
                                                    <motion.span
                                                        className="otp-box-pop"
                                                        initial={{ scale: 0.4, opacity: 0.55 }}
                                                        animate={{ scale: 1.25, opacity: 0 }}
                                                        exit={{ opacity: 0 }}
                                                        transition={{ duration: 0.45, ease: "easeOut" }}
                                                    />
                                                )}
                                            </AnimatePresence>
                                        </motion.div>
                                    ))}
                                </motion.div>

                                <div className="otp-progress">
                                    <motion.span
                                        className="otp-progress-bar"
                                        animate={{ scaleX: filledCount / OTP_LENGTH }}
                                        transition={{ type: "spring", stiffness: 260, damping: 28 }}
                                    />
                                </div>

                                <AnimatePresence mode="wait">
                                    {notice && !error && (
                                        <motion.div
                                            key={notice}
                                            className="otp-notice"
                                            initial={{ opacity: 0, y: -6 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: -6 }}
                                            transition={{ duration: 0.2 }}
                                        >
                                            {notice}
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                <AnimatePresence mode="wait">
                                    {error && (
                                        <motion.div
                                            key={error}
                                            className="otp-error"
                                            initial={{ opacity: 0, y: -6 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: -6 }}
                                            transition={{ duration: 0.2 }}
                                        >
                                            {error}
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                <motion.button
                                    type="submit"
                                    className="otp-submit"
                                    disabled={isBusy || filledCount !== OTP_LENGTH}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                >
                                    {status === "verifying" ? (
                                        <span className="otp-submit-busy">
                                            <span className="otp-spinner" />
                                            Verifying...
                                        </span>
                                    ) : (
                                        "Verify OTP"
                                    )}
                                </motion.button>

                                <button
                                    type="button"
                                    className="otp-cancel"
                                    onClick={onClose}
                                    disabled={isBusy}
                                >
                                    Cancel
                                </button>
                            </form>

                            {onResend && (
                                <div className="otp-footer">
                                    <p>Didn't receive the code?</p>
                                    <button
                                        className="otp-resend"
                                        type="button"
                                        onClick={handleResend}
                                        disabled={isBusy || resending || cooldown > 0}
                                    >
                                        {resending ? (
                                            <span className="otp-submit-busy">
                                                <span className="otp-spinner otp-spinner-accent" />
                                                Sending...
                                            </span>
                                        ) : cooldown > 0 ? (
                                            `Resend in ${cooldown}s`
                                        ) : (
                                            "Resend OTP"
                                        )}
                                    </button>
                                </div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </motion.div>
    );
}
