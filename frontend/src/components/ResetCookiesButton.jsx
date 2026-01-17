// Temporary utility to test cookie consent
// Add this button anywhere in your app to reset cookie consent

export function ResetCookiesButton() {
    const handleReset = () => {
        localStorage.removeItem('cookieConsent');
        localStorage.removeItem('cookieConsentDate');
        console.log('🍪 Cookie consent reset! Refresh the page to see the banner.');
        alert('Cookie consent reset! Refresh the page to see the banner.');
        window.location.reload();
    };

    return (
        <button
            onClick={handleReset}
            style={{
                position: 'fixed',
                bottom: '20px',
                right: '20px',
                padding: '12px 20px',
                background: '#ff6b6b',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold',
                zIndex: 99999,
                boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
            }}
        >
            🍪 Reset Cookies
        </button>
    );
}
