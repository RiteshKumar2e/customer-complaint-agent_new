import { useState, useEffect } from "react";
import Landing from "./components/Landing";
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
import { getAllComplaints } from "./api";
import { motion, AnimatePresence } from "framer-motion";
import "./App.css";
import "./styles/Profile.css";

export default function App() {
  const [page, setPage] = useState("landing");
  const [user, setUser] = useState(null);
  const [result, setResult] = useState(null);
  const [showChatbot, setShowChatbot] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(false);

  // Check for existing session and URL routes
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
    }

    // Handle deep links from email
    if (window.location.pathname === "/reset-password") {
      setPage("reset-password");
    }
  }, []);

  // Load complaints from database
  useEffect(() => {
    if (page === "dashboard" || page === "form" || page === "profile") {
      loadComplaints();
    }
  }, [page]);

  const loadComplaints = async () => {
    try {
      setLoading(true);
      const data = await getAllComplaints(user?.email || "");
      setComplaints(data.complaints || []);
    } catch (error) {
      console.error("Error loading complaints:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleComplaintSubmit = async (data) => {
    setResult(data);
    await loadComplaints(); // Reload complaints after submission

    // Redirect to profile page after a short delay to show result
    setTimeout(() => {
      navigateTo("profile");
      // Scroll to top
      window.scrollTo(0, 0);
    }, 3000);
  };

  const navigateTo = (newPage) => {
    setPage(newPage);
    if (newPage === "landing") {
      setResult(null); // Clear result when going back to landing
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    navigateTo("landing");
  };

  const handleChatToggle = () => {
    setShowChatbot(!showChatbot);
  };

  // Landing Page
  if (page === "landing") {
    return (
      <>
        <Landing
          onStart={() => user ? navigateTo("profile") : navigateTo("login")}
          onDashboard={() => user ? navigateTo("profile") : navigateTo("login")}
          onFeedback={() => setFeedbackOpen(true)}
        />
        <NotificationCenter />

        {/* Feedback Modal */}
        {feedbackOpen && (
          <Feedback onClose={() => setFeedbackOpen(false)} />
        )}
      </>
    );
  }

  // Login Page
  if (page === "login") {
    return (
      <Login
        onNavigate={navigateTo}
        onLoginSuccess={(userData) => {
          setUser(userData);
          navigateTo("profile");
        }}
      />
    );
  }

  // Signup Page
  if (page === "signup") {
    return (
      <Signup onNavigate={navigateTo} />
    );
  }

  // Forgot Password Page
  if (page === "forgot-password") {
    return (
      <ForgotPassword onNavigate={navigateTo} />
    );
  }

  // Reset Password Page
  if (page === "reset-password") {
    return (
      <ResetPassword onNavigate={navigateTo} />
    );
  }

  // Profile Page
  if (page === "profile") {
    return (
      <>
        <Profile
          user={user}
          onNavigate={navigateTo}
          onLogout={handleLogout}
          complaints={complaints}
          setComplaints={setComplaints}
        />
        {/* Standardized Chatbot - Global for Profile */}
        <motion.button
          className="chatbot-toggle"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setShowChatbot(!showChatbot)}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.6 }}
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <circle cx="12" cy="5" r="2" />
            <path d="M12 7v4" />
            <line x1="8" y1="16" x2="8" y2="16" />
            <line x1="16" y1="16" x2="16" y2="16" />
          </svg>
        </motion.button>
        <SideChatBot open={showChatbot} onClose={() => setShowChatbot(false)} />
      </>
    );
  }


  // Complaint Form Page
  return (
    <div className="app-container">
      {/* Consistent Profile-style Header for Form Page */}
      <header className="profile-header" style={{ position: 'fixed', top: 0, left: 0, right: 0, width: '100%', boxSizing: 'border-box' }}>
        <div className="header-content">
          <div className="header-left">
            <div className="logo" onClick={() => navigateTo("landing")}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
              <span>Quickfix</span>
            </div>
          </div>
          <div className="header-right">
            <button
              className="nav-btn active"
              onClick={() => navigateTo("profile")}
              style={{ padding: '0.6rem 1.2rem', borderRadius: '12px' }}
            >
              📊 Back to Profile
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="form-content" style={{ marginTop: '100px' }}>
        <ComplaintForm onResult={handleComplaintSubmit} user={user} />
        {result && (
          <div className="result-section">
            <ComplaintCard data={result} />
          </div>
        )}
      </main>

      {/* Standardized Chatbot Toggle */}
      <motion.button
        className="chatbot-toggle"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setShowChatbot(!showChatbot)}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.6 }}
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="11" width="18" height="10" rx="2" />
          <circle cx="12" cy="5" r="2" />
          <path d="M12 7v4" />
          <line x1="8" y1="16" x2="8" y2="16" />
          <line x1="16" y1="16" x2="16" y2="16" />
        </svg>
      </motion.button>

      {/* Global Side Chatbot Panel */}
      <SideChatBot
        open={showChatbot}
        onClose={() => setShowChatbot(false)}
      />

      {/* Notification System */}
      <NotificationCenter />
    </div>
  );
}