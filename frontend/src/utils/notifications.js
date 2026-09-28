// Shows a toast via <NotificationCenter />, which listens for this event
export const showNotification = (type, title, message, icon) => {
  const event = new CustomEvent("showNotification", {
    detail: { type, title, message, icon },
  });
  window.dispatchEvent(event);

  // Also show browser notification if permitted
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification(title, {
      body: message,
      icon: "https://img.icons8.com/parakeet/96/robot-machine.png",
    });
  }
};
