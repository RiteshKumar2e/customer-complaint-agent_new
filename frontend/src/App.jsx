import { useState, useEffect, useCallback } from "react";
import Landing from "./components/Landing";
import chatbotImg from "./assets/chatbot.png";
import ComplaintForm from "./components/ComplaintForm";
import ComplaintCard from "./components/ComplaintCard";
import SideChatBot from "./components/SideChatBot";
import Feedback from "./components/Feedback";
import NotificationCenter from "./components/NotificationCenter";
import Login from "./components/Login";
import Signup from "./components/Signup";
import ForgotPassword from "./components/ForgotPassword";
import ResetPassword from "./components/ResetPassword";
import Profile from "./components/Profile";
import AdminDashboard from "./components/AdminDashboard";
import AdminLoginHistory from "./components/Admin/AdminLoginHistory";
import AgentModule from "./components/Agent/AgentModule";
import AgentResolutions from "./components/Agent/AgentResolutions";
import CookiePolicy from "./components/CookiePolicy";
import ThemeToggle from "./components/ThemeToggle";
import CursorTrail from "./components/CursorTrail";
import SignInPromptModal from "./components/SignInPromptModal";
import { getAllComplaints, logoutUser } from "./api";
import { motion, AnimatePresence } from "framer-motion";
import "./App.css";
import "./styles/Profile.css";
// Sabse last import — sabhi buttons ke hover/ripple/glow effects hata kar
// unhe normal button banata hai.
import "./styles/ButtonReset.css";

export default function App() {
  const [page, setPage] = useState(() => {
    const savedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    const lastPage = localStorage.getItem("lastPage");
    const lastActivity = localStorage.getItem("lastActivity") || localStorage.getItem("sessionTimestamp");

    // Check if session has expired (Use Idle Timeout)
    if (savedUser && token && lastActivity) {
      const now = Date.now();
      const idleTime = now - parseInt(lastActivity);
      const SESSION_TIMEOUT = 20 * 60 * 1000; // 20 minutes of inactivity

      if (idleTime > SESSION_TIMEOUT) {
        // Session expired - clear everything
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        localStorage.removeItem("saved_creds"); // Optional: Keep or remove based on preference
        localStorage.removeItem("lastPage");
        localStorage.removeItem("sessionTimestamp");
        localStorage.removeItem("lastActivity");
        return "landing";
      }

      // Session still valid
      if (lastPage) {
        return lastPage;
      }
    }
    return "landing";
  });
  const [user, setUser] = useState(null);
  const [result, setResult] = useState(null);
  const [showChatbot, setShowChatbot] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [complaints, setComplaints] = useState([]);
  const [isAdminMode, setIsAdminMode] = useState(false);

  // These three are declared above the effects that call them. The session
  // timers below are registered once on mount, so they need a reference that
  // is already defined and stays stable for the life of the component.
  const navigateTo = useCallback((newPage) => {
    setPage(newPage);
    if (newPage === "landing") {
      setResult(null);
    }
  }, []);

  const handleLogout = useCallback(() => {
    // Read the email from storage rather than `user` state: the session
    // timers capture this function once, and on a mount-time expiry the
    // state hasn't been populated yet.
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      try {
        const { email } = JSON.parse(savedUser);
        if (email) {
          logoutUser(email).catch(err => console.error("Logout log error:", err));
        }
      } catch {
        // Malformed user in storage - nothing to log server-side
      }
    }
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("lastPage");
    localStorage.removeItem("sessionTimestamp");
    localStorage.removeItem("lastActivity");
    setUser(null);
    setIsAdminMode(false);
    navigateTo("landing");
  }, [navigateTo]);

  const loadComplaints = useCallback(async () => {
    if (!user?.email) return;
    try {
      const data = await getAllComplaints(user.email);
      setComplaints(data.complaints || []);
    } catch (error) {
      console.error("Error loading complaints:", error);
      setComplaints([]);
    }
  }, [user]);

  // Session timeout management
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    // Use lastActivity for validation to support sliding session
    const lastActivity = localStorage.getItem("lastActivity") || localStorage.getItem("sessionTimestamp");

    if (savedUser && token) {
      // Validate session on mount
      if (lastActivity) {
        const now = Date.now();
        const idleTime = now - parseInt(lastActivity);
        const SESSION_TIMEOUT = 20 * 60 * 1000; // 20 minutes

        if (idleTime > SESSION_TIMEOUT) {
          // Runs at most once on mount, and only to tear a dead session down
          // before anything renders against it.
          // eslint-disable-next-line react-hooks/set-state-in-effect
          handleLogout();
          return;
        }
      }

      setUser(JSON.parse(savedUser));

      // Update last activity timestamp on mount
      localStorage.setItem("lastActivity", Date.now().toString());
    }

    // Auto-logout timer - check every minute
    const checkSessionInterval = setInterval(() => {
      const currentLastActivity = localStorage.getItem("lastActivity") || localStorage.getItem("sessionTimestamp");
      const currentToken = localStorage.getItem("token");

      if (currentToken && currentLastActivity) {
        const now = Date.now();
        const idleTime = now - parseInt(currentLastActivity);
        const SESSION_TIMEOUT = 20 * 60 * 1000; // 20 minutes

        if (idleTime > SESSION_TIMEOUT) {
          handleLogout();
          alert("आपका session 20 minutes के inactivity के बाद expire हो गया है। कृपया फिर से login करें।");
        }
      }
    }, 60000); // Check every 1 minute

    // Activity tracker - update last activity on user interaction
    const updateActivity = () => {
      const currentToken = localStorage.getItem("token");
      if (currentToken) {
        localStorage.setItem("lastActivity", Date.now().toString());
      }
    };

    // Track user activity
    window.addEventListener("mousemove", updateActivity);
    window.addEventListener("keydown", updateActivity);
    window.addEventListener("click", updateActivity);
    window.addEventListener("scroll", updateActivity);

    // 🚪 Auto-logout on tab close/navigation
    const handleBeforeUnload = () => {
      const currentToken = localStorage.getItem("token");

      if (currentToken) {
        // Set a flag in sessionStorage to detect if this is a refresh
        const isRefreshing = sessionStorage.getItem("isRefreshing");

        if (!isRefreshing) {
          // This is a tab close or navigation away - clear session
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          localStorage.removeItem("saved_creds");
          localStorage.removeItem("lastPage");
          localStorage.removeItem("sessionTimestamp");
          localStorage.removeItem("lastActivity");
        }

        // Clear the refresh flag
        sessionStorage.removeItem("isRefreshing");
      }
    };

    // Set refresh flag before unload
    const handlePageHide = () => {
      // Mark as refreshing in sessionStorage (survives page reload)
      sessionStorage.setItem("isRefreshing", "true");
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("pagehide", handlePageHide);

    // Initial page routing
    if (window.location.pathname === "/reset-password") {
      setPage("reset-password");
    } else if (window.location.pathname === "/dashboard") {
      const savedUserCheck = localStorage.getItem("user");
      if (savedUserCheck) {
        setPage("profile");
      } else {
        setPage("landing");
      }
    } else if (window.location.pathname === "/feedback") {
      setPage("landing");
      setFeedbackOpen(true);
    }

    return () => {
      clearInterval(checkSessionInterval);
      window.removeEventListener("mousemove", updateActivity);
      window.removeEventListener("keydown", updateActivity);
      window.removeEventListener("click", updateActivity);
      window.removeEventListener("scroll", updateActivity);
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("pagehide", handlePageHide);
    };
    // handleLogout is stable, so this still runs only once on mount
  }, [handleLogout]);

  useEffect(() => {
    localStorage.setItem("lastPage", page);
  }, [page]);

  useEffect(() => {
    if (user && user.email) {
      // setComplaints only lands after the request resolves, so this isn't
      // the synchronous cascade the rule is guarding against.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadComplaints();
    }
  }, [user, loadComplaints]);

  const handleComplaintSubmit = async (data) => {
    setResult(data);
    await loadComplaints();
    setTimeout(() => {
      navigateTo("profile");
      window.scrollTo(0, 0);
    }, 3000);
  };

  const renderPage = () => {
    if (page === "landing") {
      return (
        <Landing
          user={user}
          onStart={() => {
            setIsAdminMode(false);
            user ? (user.role === "Admin" ? navigateTo("admin") : navigateTo("profile")) : navigateTo("login");
          }}
          onAdminLogin={() => {
            setIsAdminMode(true);
            navigateTo("login");
          }}
          onDashboard={() => user ? (user.role === "Admin" ? navigateTo("admin") : navigateTo("profile")) : navigateTo("login")}
          onFeedback={() => setFeedbackOpen(true)}
          onNavigate={navigateTo}
        />
      );
    }

    if (page === "login") {
      return (
        <Login
          onNavigate={(p) => {
            setIsAdminMode(false);
            navigateTo(p);
          }}
          onLoginSuccess={(userData) => {
            setUser(userData);
            setIsAdminMode(false);
            userData.role === "Admin" ? navigateTo("admin") : navigateTo("profile");
          }}
          isAdminMode={isAdminMode}
        />
      );
    }

    if (page === "signup") {
      return <Signup onNavigate={navigateTo} />;
    }

    if (page === "forgot-password") {
      return <ForgotPassword onNavigate={navigateTo} />;
    }

    if (page === "reset-password") {
      return <ResetPassword onNavigate={navigateTo} />;
    }

    if (page === "cookie-policy") {
      return <CookiePolicy onNavigate={navigateTo} />;
    }

    if (page === "profile") {
      return (
        <Profile
          user={user}
          onNavigate={navigateTo}
          onLogout={handleLogout}
          complaints={complaints}
          setComplaints={setComplaints}
        />
      );
    }

    if (page === "admin") {
      return (
        <AdminDashboard
          user={user}
          onNavigate={navigateTo}
          onLogout={handleLogout}
        />
      );
    }

    if (page === "login-history") {
      return (
        <div className="app-container">
          <header className="profile-header">
            <div className="header-content">
              <div className="header-left">
                <div className="logo" onClick={() => navigateTo("admin")}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                  </svg>
                  <span>Quickfix Admin</span>
                </div>
              </div>
              <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <ThemeToggle className="navbar-theme-toggle" />
                <button
                  className="nav-btn active"
                  onClick={() => navigateTo("admin")}
                >
                  📊 Back to Dashboard
                </button>
                <button
                  className="nav-btn"
                  onClick={handleLogout}
                >
                  🚪 Logout
                </button>
              </div>
            </div>
          </header>
          <AdminLoginHistory />
        </div>
      );
    }

    if (page === "agent-queue") {
      return (
        <AgentModule
          user={user}
          onNavigate={navigateTo}
          onLogout={handleLogout}
        />
      );
    }

    if (page === "agent-resolutions") {
      return (
        <AgentResolutions
          user={user}
          onNavigate={navigateTo}
          onLogout={handleLogout}
        />
      );
    }

    return (
      <div className="app-container">
        <header className="profile-header">
          <div className="header-content">
            <div className="header-left">
              <div className="logo" onClick={() => navigateTo("landing")}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
                <span>Quickfix</span>
              </div>
            </div>
            <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <ThemeToggle className="navbar-theme-toggle" />
              <button
                className="nav-btn active"
                onClick={() => navigateTo("profile")}
              >
                📊 Back to Profile
              </button>
            </div>
          </div>
        </header>

        <main className="form-content-wrapper">
          <ComplaintForm onResult={handleComplaintSubmit} user={user} />
          {result && (
            <div className="result-section">
              <ComplaintCard data={result} />
            </div>
          )}
        </main>
      </div>
    );
  };

  return (
    <>
      <CursorTrail />
      <NotificationCenter />
      {['login', 'signup', 'forgot-password', 'reset-password'].includes(page) && (
        <ThemeToggle className="fixed" />
      )}

      {renderPage()}

      {/* Sign-In Prompt Modal (Triggered after 15s on Landing Page) */}
      {page === "landing" && !user && (
        <SignInPromptModal
          onNavigate={navigateTo}
          isAuthenticated={!!user}
        />
      )}

      {(page === "landing" || page === "profile" || page === "form" || !["login", "signup", "forgot-password", "reset-password"].includes(page)) && (
        <>
          <motion.button
            className="chatbot-toggle"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setShowChatbot(!showChatbot)}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.6 }}
          >
            <img
              src={chatbotImg}
              alt="Bot"
              loading="lazy"
              width="110"
              height="110"
              style={{ color: 'transparent' }}
            />
          </motion.button>
          <SideChatBot open={showChatbot} onClose={() => setShowChatbot(false)} />
        </>
      )}

      {feedbackOpen && (
        <Feedback onClose={() => setFeedbackOpen(false)} />
      )}
    </>
  );
}
