import { motion } from 'framer-motion';
import '../styles/CookiePolicy.css';

export default function CookiePolicy({ onNavigate }) {
    return (
        <div className="cookie-policy-page">
            <div className="cookie-policy-container">
                <motion.div
                    className="cookie-policy-content"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    {/* Header */}
                    <div className="cookie-policy-header">
                        <h1 style={{ color: '#ffffff' }}>🍪 Cookie Policy</h1>
                        <p className="last-updated" style={{ color: '#9ca3af' }}>Last updated: January 21, 2026</p>
                    </div>

                    {/* Introduction */}
                    <section className="policy-section">
                        <h2 style={{ color: '#ffffff' }}>What are cookies?</h2>
                        <p style={{ color: '#d1d5db' }}>
                            Cookies are small data files placed on your device when you visit our website.
                            They help us make the website work properly and improve your experience.
                        </p>
                    </section>

                    {/* Types of cookies */}
                    <section className="policy-section">
                        <h2 style={{ color: '#ffffff' }}>Types of cookies we use</h2>

                        <div className="cookie-type">
                            <h3 style={{ color: '#c4b5fd' }}>🔒 Essential Cookies</h3>
                            <p style={{ color: '#d1d5db' }}>
                                Required for the website to function. These keep you logged in and protect your data.
                            </p>
                        </div>

                        <div className="cookie-type">
                            <h3 style={{ color: '#c4b5fd' }}>📊 Analytics Cookies</h3>
                            <p style={{ color: '#d1d5db' }}>
                                Help us understand how visitors use our website so we can improve it.
                            </p>
                        </div>

                        <div className="cookie-type">
                            <h3 style={{ color: '#c4b5fd' }}>🎯 Advertising Cookies</h3>
                            <p style={{ color: '#d1d5db' }}>
                                Used to show you relevant advertisements and measure campaign effectiveness.
                            </p>
                        </div>
                    </section>

                    {/* How to control cookies */}
                    <section className="policy-section">
                        <h2 style={{ color: '#ffffff' }}>How to control cookies</h2>
                        <p style={{ color: '#d1d5db' }}>
                            You can manage your cookie preferences through the cookie banner on our website
                            or through your browser settings.
                        </p>
                    </section>

                    {/* Footer */}
                    <div className="policy-footer">
                        <button
                            className="btn-primary"
                            onClick={() => onNavigate('landing')}
                        >
                            Return to Home
                        </button>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
