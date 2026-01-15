import { useState, useEffect, useRef } from "react";
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
import ThemeToggle from "./components/ThemeToggle";
import { getAllComplaints } from "./api";
import { motion, AnimatePresence } from "framer-motion";
import "./App.css";
import "./styles/Profile.css";

function CursorTrail() {
  const canvasRef = useRef(null);
  const mousePos = useRef({ x: 0, y: 0 });
  const targetPos = useRef({ x: 0, y: 0 });
  const particles = useRef([]);
  const [isLight, setIsLight] = useState(() => document.body.classList.contains('light-theme'));

  useEffect(() => {
    const observer = new MutationObserver(() => {
      const light = document.body.classList.contains('light-theme');
      setIsLight(light);
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });

    document.body.style.cursor = 'none';

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    let animationFrameId;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', resize);
    resize();

    // Throttling mousemove for better performance
    let lastMove = 0;
    const handleMove = (x, y) => {
      targetPos.current = { x, y };

      const now = Date.now();
      if (now - lastMove < 16) return; // ~60fps throttle
      lastMove = now;

      // Fewer but better particles
      const count = isLight ? 2 : 3;
      for (let i = 0; i < count; i++) {
        particles.current.push({
          x,
          y,
          vx: (Math.random() - 0.5) * 3,
          vy: (Math.random() - 0.5) * 3,
          life: 1.0,
          size: Math.random() * 4 + 1,
          color: isLight
            ? (Math.random() > 0.5 ? '#2563eb' : '#3b82f6')
            : (Math.random() > 0.3 ? '#00d2ff' : '#ffffff')
        });
      }

      // Keep array size small
      if (particles.current.length > 80) {
        particles.current.splice(0, particles.current.length - 80);
      }
    };

    const handleMouseMove = (e) => handleMove(e.clientX, e.clientY);
    const handleTouchMove = (e) => {
      if (e.touches.length > 0) {
        handleMove(e.touches[0].clientX, e.touches[0].clientY);
      }
    };

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Smooth lerp (fixed speed for less jitter)
      mousePos.current.x += (targetPos.current.x - mousePos.current.x) * 0.2;
      mousePos.current.y += (targetPos.current.y - mousePos.current.y) * 0.2;

      const { x, y } = mousePos.current;

      // Draw Intense Core Glow (Simplified for performance - no shadowBlur)
      const outerRadius = isLight ? 35 : 45;
      const innerRadius = 2;

      const glow = ctx.createRadialGradient(x, y, innerRadius, x, y, outerRadius);

      if (isLight) {
        glow.addColorStop(0, '#ffffff');
        glow.addColorStop(0.2, '#3b82f6');
        glow.addColorStop(0.5, 'rgba(59, 130, 246, 0.3)');
        glow.addColorStop(1, 'rgba(59, 130, 246, 0)');
      } else {
        glow.addColorStop(0, '#ffffff');
        glow.addColorStop(0.1, '#00d2ff');
        glow.addColorStop(0.4, 'rgba(0, 210, 255, 0.3)');
        glow.addColorStop(1, 'rgba(0, 210, 255, 0)');
      }

      ctx.save();
      ctx.globalCompositeOperation = isLight ? 'source-over' : 'screen';
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(x, y, outerRadius, 0, Math.PI * 2);
      ctx.fill();

      // Bright center dot
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      // Update and Draw Particles
      for (let i = particles.current.length - 1; i >= 0; i--) {
        const p = particles.current[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.02;
        p.size *= 0.97;

        if (p.life <= 0 || p.size < 0.5) {
          particles.current.splice(i, 1);
          continue;
        }

        ctx.globalAlpha = p.life * 0.8;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1.0;

      animationFrameId = requestAnimationFrame(render);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('touchmove', handleTouchMove, { passive: true });
    render();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
      observer.disconnect();
      document.body.style.cursor = 'default';
    };
  }, [isLight]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 10001,
        transition: 'opacity 0.5s ease-in-out'
      }}
    />
  );
}

export default function App() {
  const [page, setPage] = useState(() => {
    // Initial page load from localStorage if logged in
    const savedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    const lastPage = localStorage.getItem("lastPage");

    if (savedUser && token && lastPage) {
      return lastPage;
    }
    return "landing";
  });
  const [user, setUser] = useState(null);
  const [result, setResult] = useState(null);
  const [showChatbot, setShowChatbot] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isAdminMode, setIsAdminMode] = useState(false);

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
    } else if (window.location.pathname === "/dashboard") {
      // If user is logged in, show profile, else landing will handle sign-in button
      const savedUser = localStorage.getItem("user");
      if (savedUser) {
        setPage("profile");
      } else {
        setPage("landing");
      }
    } else if (window.location.pathname === "/feedback") {
      setPage("landing");
      setFeedbackOpen(true);
    }
  }, []);

  // Save lastPage to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("lastPage", page);
  }, [page]);

  // Load complaints from database
  useEffect(() => {
    if ((page === "dashboard" || page === "form" || page === "profile") && user?.email) {
      loadComplaints();
    }
  }, [page, user?.email]);

  const loadComplaints = async () => {
    if (!user?.email) return;
    try {
      setLoading(true);
      const data = await getAllComplaints(user.email);
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
    localStorage.removeItem("lastPage");
    setUser(null);
    setIsAdminMode(false); // Reset admin mode on logout
    navigateTo("landing");
  };

  const handleChatToggle = () => {
    setShowChatbot(!showChatbot);
  };

  // Landing Page
  if (page === "landing") {
    return (
      <>
        <CursorTrail />
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
        />
        <NotificationCenter />

        {/* Floating Chatbot Toggle for Landing */}
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
      <>
        <ThemeToggle className="fixed" />
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
      </>
    );
  }

  // Signup Page
  if (page === "signup") {
    return (
      <>
        <ThemeToggle className="fixed" />
        <Signup onNavigate={navigateTo} />
      </>
    );
  }

  // Forgot Password Page
  if (page === "forgot-password") {
    return (
      <>
        <ThemeToggle className="fixed" />
        <ForgotPassword onNavigate={navigateTo} />
      </>
    );
  }

  // Reset Password Page
  if (page === "reset-password") {
    return (
      <>
        <ThemeToggle className="fixed" />
        <ResetPassword onNavigate={navigateTo} />
      </>
    );
  }

  // Profile Page
  if (page === "profile") {
    return (
      <>
        <CursorTrail />
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
    );
  }


  // Admin Dashboard Page
  if (page === "admin") {
    return (
      <>
        <CursorTrail />
        <AdminDashboard
          user={user}
          onNavigate={navigateTo}
          onLogout={handleLogout}
        />
      </>
    );
  }

  // Complaint Form Page
  return (
    <>
      <div className="app-container">
        <CursorTrail />
        {/* Consistent Profile-style Header for Form Page */}
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

        {/* Main Content */}
        <main className="form-content-wrapper">
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
          <img src={chatbotImg} alt="AI Assistant" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
        </motion.button>

        {/* Global Side Chatbot Panel */}
        <SideChatBot
          open={showChatbot}
          onClose={() => setShowChatbot(false)}
        />

        {/* Notification System */}
        <NotificationCenter />
      </div>
    </>
  );
}
