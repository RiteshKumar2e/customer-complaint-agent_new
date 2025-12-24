import { useState, useEffect } from "react";
import Landing from "./components/Landing";
import ComplaintForm from "./components/ComplaintForm";
import ComplaintCard from "./components/ComplaintCard";
import Dashboard from "./components/Dashboard";
import SideChatBot from "./components/SideChatBot";
import Feedback from "./components/Feedback";
import NotificationCenter from "./components/NotificationCenter";
import Login from "./components/Login";
import Signup from "./components/Signup";
import { getAllComplaints } from "./api";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("landing");
  const [user, setUser] = useState(null);
  const [result, setResult] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(false);

  // Check for existing session
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  // Load complaints from database
  useEffect(() => {
    if (page === "dashboard" || page === "form") {
      loadComplaints();
    }
  }, [page]);

  const loadComplaints = async () => {
    try {
      setLoading(true);
      const data = await getAllComplaints();
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

  const handleChatToggle = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    setChatOpen(prev => !prev);
  };

  // Landing Page
  if (page === "landing") {
    return (
      <>
        <Landing
          onStart={() => user ? navigateTo("form") : navigateTo("login")}
          onDashboard={() => user ? navigateTo("dashboard") : navigateTo("login")}
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
          navigateTo("form");
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

  // Forgot Password Page Placeholder
  if (page === "forgot-password") {
    return (
      <div className="auth-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
        <div className="auth-content" style={{ maxWidth: '400px', height: 'auto', borderRadius: '20px' }}>
          <h2 className="auth-title">Reset Password</h2>
          <p className="auth-subtitle">Instruction to reset your password have been sent to your email.</p>
          <button className="auth-submit" style={{ marginTop: '1.5rem' }} onClick={() => navigateTo("login")}>Back to Login</button>
        </div>
      </div>
    );
  }

  // Dashboard Page
  if (page === "dashboard") {
    return (
      <>
        <Dashboard
          onNavigate={navigateTo}
          onFeedback={() => setFeedbackOpen(true)}
          onLogout={handleLogout}
          user={user}
          complaints={complaints}
          setComplaints={setComplaints}
          loading={loading}
        />

        {/* Floating AI Chat Button */}
        <button
          type="button"
          className="chat-fab"
          onClick={handleChatToggle}
          aria-label="Toggle AI Chat Assistant"
          title="AI Assistant"
        >
          🤖
        </button>

        {/* Side Chatbot Panel */}
        <SideChatBot
          open={chatOpen}
          onClose={() => setChatOpen(false)}
        />

        <NotificationCenter />

        {/* Feedback Modal */}
        {feedbackOpen && (
          <Feedback onClose={() => setFeedbackOpen(false)} />
        )}
      </>
    );
  }

  // Complaint Form Page
  return (
    <div className="app-container">
      {/* Navigation Header */}
      <header className="app-header">
        <div className="header-brand">
          <h1>⚡ Quickfix</h1>
          <p className="header-subtitle">AI-Powered Complaint Resolution</p>
        </div>
        <nav className="header-buttons">
          {user && (
            <div className="user-profile-lite" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginRight: '15px' }}>
              <span style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>{user.full_name || user.email}</span>
              <button
                className="header-btn logout-btn-lite"
                onClick={handleLogout}
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem', background: 'rgba(255,255,255,0.05)' }}
              >
                Logout
              </button>
            </div>
          )}
          <button
            type="button"
            className="header-btn"
            onClick={() => setFeedbackOpen(true)}
            aria-label="Send Feedback"
          >
            � Feedback
          </button>
          <button
            type="button"
            className={`header-btn ${page === 'dashboard' ? 'active' : ''}`}
            onClick={() => navigateTo("dashboard")}
            aria-label="View Dashboard"
          >
            📊 Dashboard
          </button>
          <button
            type="button"
            className="header-btn"
            onClick={() => navigateTo("landing")}
            aria-label="Go Home"
          >
            🏠 Home
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main className="form-content">
        <ComplaintForm onResult={handleComplaintSubmit} />
        {result && (
          <div className="result-section">
            <ComplaintCard data={result} />
          </div>
        )}
      </main>

      {/* Floating AI Chat Button */}
      <button
        type="button"
        className="chat-fab"
        onClick={handleChatToggle}
        aria-label="Toggle AI Chat Assistant"
        title="AI Assistant"
      >
        🤖
      </button>

      {/* Side Chatbot Panel */}
      <SideChatBot
        open={chatOpen}
        onClose={() => setChatOpen(false)}
      />

      {/* Notification System */}
      <NotificationCenter />

      {/* Feedback Modal */}
      {feedbackOpen && (
        <Feedback onClose={() => setFeedbackOpen(false)} />
      )}
    </div>
  );
}