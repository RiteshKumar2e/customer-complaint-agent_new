import { useState, useEffect } from "react";
import "../styles/NotificationCenter.css";

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Listen for notification events
    const handleNotification = (event) => {
      const notification = {
        id: Date.now(),
        ...event.detail,
      };
      setNotifications((prev) => [...prev, notification]);

      // Auto-remove notification after 5 seconds
      setTimeout(() => {
        setNotifications((prev) =>
          prev.filter((notif) => notif.id !== notification.id)
        );
      }, 5000);
    };

    window.addEventListener("showNotification", handleNotification);
    return () => window.removeEventListener("showNotification", handleNotification);
  }, []);

  const removeNotification = (id) => {
    setNotifications((prev) => prev.filter((notif) => notif.id !== id));
  };

  return (
    <div className="notification-center">
      {notifications.map((notif) => (
        <div
          key={notif.id}
          className={`notification notification-${notif.type}`}
          onClick={() => removeNotification(notif.id)}
        >
          <div className="notification-icon">{notif.icon}</div>
          <div className="notification-content">
            <div className="notification-title">{notif.title}</div>
            {notif.message && (
              <div className="notification-message">{notif.message}</div>
            )}
          </div>
          <button
            className="notification-close"
            onClick={(e) => {
              e.stopPropagation();
              removeNotification(notif.id);
            }}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
