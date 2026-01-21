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
                        <h1>🍪 Cookie Policy</h1>
                        <p className="last-updated">Last updated: January 21, 2026</p>
                    </div>

                    {/* Introduction */}
                    <section className="policy-section">
                        <h2>What are cookies?</h2>
                        <p>
                            Cookies are small data files placed on your device when you visit our website.
                            They help us make the website work properly and improve your experience.
                        </p>
                    </section>

                    {/* Types of cookies */}
                    <section className="policy-section">
                        <h2>Types of cookies we use</h2>

                        <div className="cookie-type">
                            <h3>🔒 Essential Cookies</h3>
                            <p>
                                Required for the website to function. These keep you logged in and protect your data.
                            </p>
                        </div>

                        <div className="cookie-type">
                            <h3>📊 Analytics Cookies</h3>
                            <p>
                                Help us understand how visitors use our website so we can improve it.
                            </p>
                        </div>

                        <div className="cookie-type">
                            <h3>🎯 Advertising Cookies</h3>
                            <p>
                                Used to show you relevant advertisements and measure campaign effectiveness.
                            </p>
                        </div>
                    </section>

                    {/* How to control cookies */}
                    <section className="policy-section">
                        <h2>How to control cookies</h2>
                        <p>
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
