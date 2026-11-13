import { useState, useEffect, useCallback, lazy, Suspense } from "react";
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
import ThemeToggle from "./components/ThemeToggle";
import CursorTrail from "./components/CursorTrail";
import SignInPromptModal from "./components/SignInPromptModal";
import { getAllComplaints, logoutUser, getMe, session } from "./api";
import { homePageFor } from "./utils/validation";
import { motion, AnimatePresence } from "framer-motion";
import "./App.css";
import "./styles/Profile.css";
// Sabse last import — sabhi buttons ke hover/ripple/glow effects hata kar
// unhe normal button banata hai.
import "./styles/ButtonReset.css";
// Mobile layout fixes - must stay the last stylesheet.
import "./styles/Mobile.css";
import Logo from "./components/Logo";
import NotFound from "./components/NotFound";

// Role dashboards load on demand so the landing/login pages stay light.
const Profile = lazy(() => import("./components/Profile"));
const AdminDashboard = lazy(() => import("./components/AdminDashboard"));
const AdminLoginHistory = lazy(() => import("./components/Admin/AdminLoginHistory"));
const AgentModule = lazy(() => import("./components/Agent/AgentModule"));
const AgentResolutions = lazy(() => import("./components/Agent/AgentResolutions"));
const AdminConsole = lazy(() => import("./components/Admin/AdminConsole"));
const CookiePolicy = lazy(() => import("./components/CookiePolicy"));

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
  const [signupPrefill, setSignupPrefill] = useState(null);

  const navigateTo = useCallback((newPage, prefill = null) => {
    if (newPage === "signup") setSignupPrefill(prefill);
    setPage(newPage);
    if (newPage === "landing") {
      setResult(null);
    }
  }, []);

  // Keep the address bar clean: never leave a "#section" in the URL. If an old
  // link points at a section, scroll to it once, then drop the hash.
  useEffect(() => {
    const { hash, pathname, search } = window.location;
    if (!hash) return;
    const target = document.getElementById(decodeURIComponent(hash.slice(1)));
    if (target) setTimeout(() => target.scrollIntoView({ behavior: "smooth" }), 300);
    window.history.replaceState(window.history.state, "", pathname + search);
  }, []);

  const handleLogout = useCallback(() => {
    // Revoke the session server-side (access + refresh token); clears storage either way.
    logoutUser().catch(() => {});
    session.clear();
    setUser(null);
    setIsAdminMode(false);
    navigateTo("landing");
  }, [navigateTo]);

  // A refresh failure anywhere in the app ends the session cleanly.
  useEffect(() => {
    const onExpired = () => {
      setUser(null);
      setPage("login");
    };
    window.addEventListener("qf:session-expired", onExpired);
    return () => window.removeEventListener("qf:session-expired", onExpired);
  }, []);

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
      // The stored copy is only a cache: confirm identity and role with the server.
      getMe().then((fresh) => {
        session.setUser(fresh);
        setUser(fresh);
      }).catch(() => {});

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
      const savedUserCheck = session.user;
      setPage(savedUserCheck ? homePageFor(savedUserCheck) : "landing");
    } else if (window.location.pathname === "/feedback") {
      setPage("landing");
      setFeedbackOpen(true);
    } else if (!["/", "/index.html", ""].includes(window.location.pathname)) {
      setPage("not-found");
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
    if (page !== "not-found") localStorage.setItem("lastPage", page);
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

  // Route guard: which roles may open which page. The API enforces the same rules.
  const PAGE_ROLES = {
    profile: ["customer"],
    form: ["customer"],
    admin: ["admin"],
    "login-history": ["admin"],
    "admin-console": ["admin"],
    "agent-queue": ["agent", "admin"],
    "agent-resolutions": ["agent", "admin"],
  };

  const renderPage = () => {
    const allowed = PAGE_ROLES[page];
    if (allowed) {
      const current = user || session.user;
      if (!current || !session.access) {
        return <Login onNavigate={navigateTo} onLoginSuccess={(u) => { setUser(u); navigateTo(homePageFor(u)); }} isAdminMode={false} />;
      }
      if (!allowed.includes(current.role)) {
        const home = homePageFor(current);
        if (home !== page) setTimeout(() => navigateTo(home), 0);
        return null;
      }
    }
    if (page === "landing") {
      return (
        <Landing
          user={user}
          onStart={() => {
            setIsAdminMode(false);
            user ? navigateTo(homePageFor(user)) : navigateTo("login");
          }}
          onAdminLogin={() => {
            setIsAdminMode(true);
            navigateTo("login");
          }}
          onDashboard={() => user ? navigateTo(homePageFor(user)) : navigateTo("login")}
          onFeedback={() => setFeedbackOpen(true)}
          onNavigate={navigateTo}
        />
      );
    }

    if (page === "not-found") {
      return (
        <NotFound onHome={() => { window.history.replaceState(null, "", "/"); navigateTo("landing"); }} />
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
            navigateTo(homePageFor(userData));
          }}
          isAdminMode={isAdminMode}
        />
      );
    }

    if (page === "signup") {
      return (
        <Signup
          onNavigate={navigateTo}
          prefill={signupPrefill}
          onRegistered={(newUser) => {
            setUser(newUser);
            navigateTo(homePageFor(newUser));
          }}
        />
      );
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
                  <Logo height={28} /><span className="qf-area-badge">Admin</span>
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

    if (page === "admin-console") {
      return (
        <div className="app-container">
          <header className="profile-header">
            <div className="header-content">
              <div className="header-left">
                <Logo height={28} onClick={() => navigateTo("admin")} /><span className="qf-area-badge">Admin</span>
              </div>
              <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <ThemeToggle className="navbar-theme-toggle" />
                <button className="nav-btn" onClick={() => navigateTo("admin")}>Complaints</button>
                <button className="nav-btn" onClick={handleLogout}>Logout</button>
              </div>
            </div>
          </header>
          <div className="qf-under-header"><AdminConsole user={user || session.user} /></div>
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
                <Logo height={28} />
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

      <Suspense fallback={<div className="qf-page-loading" role="status">Loading…</div>}>
        {renderPage()}
      </Suspense>

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
