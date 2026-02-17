import { useEffect } from 'react';
import '../styles/CustomNotification.css';

export default function CustomNotification({ message, type = 'info', onClose, duration = 5000 }) {
    useEffect(() => {
        if (duration > 0) {
            const timer = setTimeout(() => {
                onClose();
            }, duration);
            return () => clearTimeout(timer);
        }
    }, [duration, onClose]);

    const getIcon = () => {
        switch (type) {
            case 'error':
                return '⚠️';
            case 'success':
                return '✅';
            case 'warning':
                return '⚡';
            case 'info':
            default:
                return 'ℹ️';
        }
    };

    return (
        <div className={`custom-notification ${type}`}>
            <div className="notification-content">
                <span className="notification-icon">{getIcon()}</span>
                <p className="notification-message">{message}</p>
                <button className="notification-close" onClick={onClose} aria-label="Close notification">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div className="notification-progress"></div>
        </div>
    );
}
