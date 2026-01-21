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
                        <button
                            className="back-button"
                            onClick={() => onNavigate('landing')}
                            aria-label="Go back"
                        >
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M19 12H5M12 19l-7-7 7-7" />
                            </svg>
                            Back
                        </button>
                        <h1>🍪 Cookie Policy</h1>
                        <p className="last-updated">Last updated: January 21, 2026</p>
                    </div>

                    {/* Introduction */}
                    <section className="policy-section">
                        <h2>Introduction</h2>
                        <p>
                            This Cookie Policy explains how Quickfix ("we", "us", or "our") uses cookies and similar
                            technologies to recognize you when you visit our website. It explains what these technologies
                            are and why we use them, as well as your rights to control our use of them.
                        </p>
                    </section>

                    {/* What are cookies */}
                    <section className="policy-section">
                        <h2>What are cookies?</h2>
                        <p>
                            Cookies are small data files that are placed on your computer or mobile device when you visit
                            a website. Cookies are widely used by website owners in order to make their websites work, or
                            to work more efficiently, as well as to provide reporting information.
                        </p>
                        <p>
                            Cookies set by the website owner (in this case, Quickfix) are called "first-party cookies".
                            Cookies set by parties other than the website owner are called "third-party cookies".
                            Third-party cookies enable third-party features or functionality to be provided on or through
                            the website (e.g., advertising, interactive content, and analytics).
                        </p>
                    </section>

                    {/* Why we use cookies */}
                    <section className="policy-section">
                        <h2>Why do we use cookies?</h2>
                        <p>
                            We use first-party and third-party cookies for several reasons. Some cookies are required for
                            technical reasons in order for our website to operate, and we refer to these as "essential" or
                            "strictly necessary" cookies. Other cookies enable us to track and target the interests of our
                            users to enhance the experience on our website. Third parties serve cookies through our website
                            for advertising, analytics, and other purposes.
                        </p>
                    </section>

                    {/* Types of cookies */}
                    <section className="policy-section">
                        <h2>Types of cookies we use</h2>

                        <div className="cookie-type">
                            <h3>🔒 Essential Cookies</h3>
                            <p>
                                These cookies are strictly necessary to provide you with services available through our
                                website and to use some of its features, such as access to secure areas. Because these
                                cookies are strictly necessary to deliver the website, you cannot refuse them without
                                impacting how our website functions.
                            </p>
                            <ul>
                                <li><strong>Session cookies:</strong> Keep you logged in during your visit</li>
                                <li><strong>Security cookies:</strong> Protect your account and data</li>
                                <li><strong>Preference cookies:</strong> Remember your settings and choices</li>
                            </ul>
                        </div>

                        <div className="cookie-type">
                            <h3>📊 Analytics Cookies</h3>
                            <p>
                                These cookies help us understand how visitors interact with our website by collecting and
                                reporting information anonymously. This helps us improve our website and services.
                            </p>
                            <ul>
                                <li><strong>Usage data:</strong> Pages visited, time spent, and navigation patterns</li>
                                <li><strong>Performance metrics:</strong> Page load times and technical errors</li>
                                <li><strong>User behavior:</strong> How you interact with features and content</li>
                            </ul>
                        </div>

                        <div className="cookie-type">
                            <h3>🎯 Advertising Cookies</h3>
                            <p>
                                These cookies are used to make advertising messages more relevant to you. They perform
                                functions like preventing the same ad from continuously reappearing, ensuring that ads are
                                properly displayed, and in some cases selecting advertisements that are based on your interests.
                            </p>
                            <ul>
                                <li><strong>Targeted ads:</strong> Show you relevant advertisements</li>
                                <li><strong>Ad frequency:</strong> Control how often you see specific ads</li>
                                <li><strong>Campaign effectiveness:</strong> Measure the success of our marketing campaigns</li>
                            </ul>
                        </div>
                    </section>

                    {/* How to control cookies */}
                    <section className="policy-section">
                        <h2>How can you control cookies?</h2>
                        <p>
                            You have the right to decide whether to accept or reject cookies. You can exercise your cookie
                            preferences by clicking on the appropriate opt-out links provided in the cookie consent banner
                            that appears when you first visit our website.
                        </p>
                        <p>
                            You can also set or amend your web browser controls to accept or refuse cookies. If you choose
                            to reject cookies, you may still use our website though your access to some functionality and
                            areas of our website may be restricted.
                        </p>

                        <div className="browser-controls">
                            <h4>Browser-specific cookie controls:</h4>
                            <ul>
                                <li><strong>Chrome:</strong> Settings → Privacy and security → Cookies and other site data</li>
                                <li><strong>Firefox:</strong> Options → Privacy & Security → Cookies and Site Data</li>
                                <li><strong>Safari:</strong> Preferences → Privacy → Cookies and website data</li>
                                <li><strong>Edge:</strong> Settings → Cookies and site permissions → Cookies and site data</li>
                            </ul>
                        </div>
                    </section>

                    {/* Data retention */}
                    <section className="policy-section">
                        <h2>How long do we keep cookies?</h2>
                        <p>
                            The length of time a cookie will stay on your computer or mobile device depends on whether it
                            is a "persistent" or "session" cookie. Session cookies will only stay on your device until you
                            stop browsing. Persistent cookies stay on your computer or mobile device until they expire or
                            are deleted.
                        </p>
                        <ul>
                            <li><strong>Session cookies:</strong> Deleted when you close your browser</li>
                            <li><strong>Persistent cookies:</strong> Remain for up to 12 months or until manually deleted</li>
                        </ul>
                    </section>

                    {/* Updates to policy */}
                    <section className="policy-section">
                        <h2>Updates to this Cookie Policy</h2>
                        <p>
                            We may update this Cookie Policy from time to time in order to reflect changes to the cookies
                            we use or for other operational, legal, or regulatory reasons. Please therefore revisit this
                            Cookie Policy regularly to stay informed about our use of cookies and related technologies.
                        </p>
                    </section>

                    {/* Contact */}
                    <section className="policy-section">
                        <h2>Contact Us</h2>
                        <p>
                            If you have any questions about our use of cookies or other technologies, please contact us at:
                        </p>
                        <div className="contact-info">
                            <p><strong>Email:</strong> privacy@quickfix.com</p>
                            <p><strong>Phone:</strong> +91 1234567890</p>
                            <p><strong>Address:</strong> Quickfix Technologies, India</p>
                        </div>
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
