import { useState, useEffect } from "react";
import Landing from "./components/Landing";
import ComplaintForm from "./components/ComplaintForm";
import ComplaintCard from "./components/ComplaintCard";
import Dashboard from "./components/Dashboard";
import SideChatBot from "./components/SideChatBot";
import NotificationCenter from "./components/NotificationCenter";
import { getAllComplaints } from "./api";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("landing");
  const [result, setResult] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(false);

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
          onStart={() => navigateTo("form")} 
          onDashboard={() => navigateTo("dashboard")} 
        />
        <NotificationCenter />
      </>
    );
  }

  // Dashboard Page
  if (page === "dashboard") {
    return (
      <>
        <Dashboard 
          onNavigate={navigateTo} 
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
          <button 
            type="button"
            className={`header-btn ${page === 'form' ? 'active' : ''}`}
            onClick={() => navigateTo("form")}
            aria-label="Report Complaint"
          >
            📝 Report
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
    </div>
  );
}