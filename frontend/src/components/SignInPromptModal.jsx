import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, Zap, Shield, TrendingUp, Cpu, MessageSquare, BarChart2 } from 'lucide-react';
import CustomNotification from './CustomNotification';
import '../styles/SignInPromptModal.css';

const SignInPromptModal = ({ onNavigate, isAuthenticated }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
    const [notification, setNotification] = useState(null); // Custom notification state

    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    useEffect(() => {
        // Only show modal if user is NOT logged in
        if (!isAuthenticated) {
            // Show modal after 20 seconds (as per "20 section" request)
            const timer = setTimeout(() => {
                setIsVisible(true);
            }, 60000);

            return () => clearTimeout(timer);
        }
    }, [isAuthenticated]);

    const handleSignIn = () => {
        setIsVisible(false);
        onNavigate('login');
    };

    const handleClose = () => {
        // Show custom notification instead of alert
        setNotification({
            message: "Sign in is mandatory to access all enterprise features of Quickfix AI!",
            type: "warning"
        });
    };

    const features = [
        {
            icon: <Sparkles size={22} />,
            title: "AI Powered Assistant",
            description: "Advanced AI agents to resolve your issues in seconds"
        },
        {
            icon: <Zap size={22} />,
            title: "Smart Complaint System",
            description: "Automated classification and surgical priority detection"
        },
        {
            icon: <BarChart2 size={22} />,
            title: "My Complaints History",
            description: "Track and manage all your resolutions in one secure place"
        },
        {
            icon: <TrendingUp size={22} />,
            title: "Resolution Insights",
            description: "Predictive satisfaction and deep sentiment analysis"
        }
    ];

    return (
        <AnimatePresence>
            {isVisible && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        className="signin-prompt-backdrop"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={handleClose}
                    />

                    {/* Modal */}
                    <motion.div
                        className="signin-prompt-modal"
                        initial={{ opacity: 0, scale: 0.9, y: 20, x: '-50%' }}
                        animate={{ opacity: 1, scale: 1, y: 0, x: '-50%' }}
                        exit={{ opacity: 0, scale: 0.9, y: 20, x: '-50%' }}
                        transition={{
                            type: "spring",
                            damping: 20,
                            stiffness: 300,
                            duration: 0.5
                        }}
                        style={{
                            left: '50%',
                        }}
                    >
                        <button
                            className="signin-prompt-close"
                            onClick={handleClose}
                            aria-label="Close"
                        >
                            <X size={18} />
                        </button>

                        <div className="signin-prompt-header">
                            <div className="signin-prompt-icon-wrapper">
                                <Sparkles className="signin-prompt-icon" size={32} />
                            </div>
                            <h2>Unlock Full Access</h2>
                            <p>Sign in to experience the power of Agentic Reasoning clusters.</p>
                        </div>

                        <div className="signin-prompt-features">
                            {features.map((feature, index) => (
                                <motion.div
                                    key={index}
                                    className="signin-prompt-feature"
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.2 + (index * 0.1) }}
                                >
                                    <div className="feature-icon">
                                        {feature.icon}
                                    </div>
                                    <div className="feature-content">
                                        <h3>{feature.title}</h3>
                                        <p>{feature.description}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>

                        <div className="signin-prompt-actions">
                            <button
                                className="btn-signin-primary"
                                onClick={handleSignIn}
                            >
                                Get Started Now <Zap size={18} fill="currentColor" />
                            </button>
                        </div>
                    </motion.div>

                    {/* Custom Notification */}
                    {notification && (
                        <CustomNotification
                            message={notification.message}
                            type={notification.type}
                            onClose={() => setNotification(null)}
                        />
                    )}
                </>
            )}
        </AnimatePresence>
    );
};

export default SignInPromptModal;
