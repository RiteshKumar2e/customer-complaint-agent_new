import { useState, useEffect } from 'react';
import '../styles/CookieConsent.css';

export default function CookieConsent() {
    const [showBanner, setShowBanner] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [preferences, setPreferences] = useState({
        essential: true,
        analytics: false,
        advertising: false
    });

    useEffect(() => {
        // Check if user has already accepted/rejected cookies
        const cookieConsent = localStorage.getItem('cookieConsent');
        if (!cookieConsent) {
            // Show banner after a short delay for better UX
            setTimeout(() => setShowBanner(true), 1000);
        } else {
            // Load saved preferences
            const saved = JSON.parse(cookieConsent);
            setPreferences(saved);
        }
    }, []);

    const handleAcceptAll = () => {
        const allAccepted = {
            essential: true,
            analytics: true,
            advertising: true
        };
        setPreferences(allAccepted);
        localStorage.setItem('cookieConsent', JSON.stringify(allAccepted));
        localStorage.setItem('cookieConsentDate', new Date().toISOString());
        setShowBanner(false);
        setShowSettings(false);
    };

    const handleRejectAll = () => {
        const onlyEssential = {
            essential: true,
            analytics: false,
            advertising: false
        };
        setPreferences(onlyEssential);
        localStorage.setItem('cookieConsent', JSON.stringify(onlyEssential));
        localStorage.setItem('cookieConsentDate', new Date().toISOString());
        setShowBanner(false);
        setShowSettings(false);
    };

    const handleConfirm = () => {
        localStorage.setItem('cookieConsent', JSON.stringify(preferences));
        localStorage.setItem('cookieConsentDate', new Date().toISOString());
        setShowBanner(false);
        setShowSettings(false);
    };

    const togglePreference = (key) => {
        if (key === 'essential') return; // Essential cookies cannot be disabled
        setPreferences(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    if (!showBanner) return null;

    return (
        <>
            {/* Overlay */}
            {showBanner && (
                <div className="cookie-overlay" onClick={() => setShowBanner(false)} />
            )}

            {/* Cookie Banner */}
            <div className={`cookie-consent-banner ${showSettings ? 'settings-open' : ''}`}>
                {!showSettings ? (
                    // Main Banner
                    <div className="cookie-banner-content">
                        <div className="cookie-header">
                            <div className="cookie-icon">🍪</div>
                            <h3>We care about your privacy</h3>
                        </div>

                        <p className="cookie-description">
                            This website uses cookies that are needed for the site to work properly and to get data on how you interact with it, as well as for marketing purposes. By accepting, you agree to store cookies on your device for ad targeting, personalization, and analytics as described in our{' '}
                            <button
                                className="cookie-link"
                                onClick={() => window.open('/cookie-policy', '_blank')}
                            >
                                Cookie policy
                            </button>.
                        </p>

                        <div className="cookie-actions">
                            <button className="btn-cookie-primary" onClick={handleAcceptAll}>
                                Accept all
                            </button>
                            <button className="btn-cookie-secondary" onClick={handleRejectAll}>
                                Reject all
                            </button>
                            <button className="btn-cookie-settings" onClick={() => setShowSettings(true)}>
                                Cookie settings
                            </button>
                        </div>
                    </div>
                ) : (
                    // Settings Panel
                    <div className="cookie-settings-content">
                        <div className="cookie-settings-header">
                            <h3>Cookie settings</h3>
                            <button className="cookie-close" onClick={() => setShowSettings(false)}>
                                ✕
                            </button>
                        </div>

                        <p className="cookie-settings-description">
                            Change your cookie preferences for each category of cookies. To find out more, read our{' '}
                            <button
                                className="cookie-link"
                                onClick={() => window.open('/cookie-policy', '_blank')}
                            >
                                Cookie policy
                            </button>.
                        </p>

                        <div className="cookie-categories">
                            {/* Essential Cookies */}
                            <div className="cookie-category">
                                <div className="category-header">
                                    <div className="category-title">
                                        <span className="category-icon">▼</span>
                                        <h4>Essential cookies</h4>
                                    </div>
                                    <span className="category-status always-on">Always on</span>
                                </div>
                                <p className="category-description">
                                    These cookies are needed for our website to function and be secure.
                                </p>
                            </div>

                            {/* Analytics Cookies */}
                            <div className="cookie-category">
                                <div className="category-header">
                                    <div className="category-title">
                                        <span className="category-icon">▼</span>
                                        <h4>Analytics cookies</h4>
                                    </div>
                                    <label className="cookie-toggle">
                                        <input
                                            type="checkbox"
                                            checked={preferences.analytics}
                                            onChange={() => togglePreference('analytics')}
                                        />
                                        <span className="toggle-slider"></span>
                                    </label>
                                </div>
                                <p className="category-description">
                                    Help us understand how visitors interact with our website to improve user experience.
                                </p>
                            </div>

                            {/* Advertising Cookies */}
                            <div className="cookie-category">
                                <div className="category-header">
                                    <div className="category-title">
                                        <span className="category-icon">▼</span>
                                        <h4>Advertising cookies</h4>
                                    </div>
                                    <label className="cookie-toggle">
                                        <input
                                            type="checkbox"
                                            checked={preferences.advertising}
                                            onChange={() => togglePreference('advertising')}
                                        />
                                        <span className="toggle-slider"></span>
                                    </label>
                                </div>
                                <p className="category-description">
                                    Used to deliver personalized advertisements relevant to you and your interests.
                                </p>
                            </div>
                        </div>

                        <div className="cookie-settings-actions">
                            <button className="btn-cookie-confirm" onClick={handleConfirm}>
                                Confirm
                            </button>
                            <button className="btn-cookie-accept" onClick={handleAcceptAll}>
                                Accept all
                            </button>
                            <button className="btn-cookie-reject" onClick={handleRejectAll}>
                                Reject all
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
