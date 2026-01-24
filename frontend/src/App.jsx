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
import CookiePolicy from "./components/CookiePolicy";
import ThemeToggle from "./components/ThemeToggle";
import { getAllComplaints } from "./api";
import { motion, AnimatePresence } from "framer-motion";
import "./App.css";
import "./styles/Profile.css";

function CursorTrail() {
  const canvasRef = useRef(null);
  const mousePos = useRef({ x: 0, y: 0 });
  const targetPos = useRef({ x: 0, y: 0 });
  const velocity = useRef({ x: 0, y: 0 });
  const particles = useRef([]);
  const [isLight, setIsLight] = useState(() => document.body.classList.contains('light-theme'));

  useEffect(() => {
    document.body.classList.add('custom-cursor-active');

    const observer = new MutationObserver(() => {
      setIsLight(document.body.classList.contains('light-theme'));
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });

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

    let lastMove = 0;
    const handleMove = (x, y, isTouch = false) => {
      const dx = x - targetPos.current.x;
      const dy = y - targetPos.current.y;
      velocity.current = { x: dx, y: dy };
      targetPos.current = { x, y };

      const now = Date.now();
      const throttleLimit = isTouch ? 20 : 16;
      if (now - lastMove < throttleLimit) return;
      lastMove = now;

      const speed = Math.sqrt(dx * dx + dy * dy);
      // Spawn more particles when moving fast
      const baseCount = isTouch ? 2 : 3;
      const count = Math.min(baseCount + Math.floor(speed / 9), 9);

      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const force = Math.random() * 2;
        particles.current.push({
          x, y,
          vx: (dx * 0.1) + Math.cos(angle) * force,
          vy: (dy * 0.1) + Math.sin(angle) * force,
          life: 1.0,
          orbit: Math.random() * 0.1,
          angle: Math.random() * Math.PI * 2,
          size: Math.random() * (isTouch ? 3 : 5) + (speed * 0.05) + 1,
          color: isLight
            ? (Math.random() > 0.5 ? '#2563eb' : '#60a5fa')
            : (Math.random() > 0.4 ? '#00d2ff' : '#ffffff'),
          shimmer: Math.random() * 10
        });
      }

      const maxParticles = isTouch ? 80 : 120;
      if (particles.current.length > maxParticles) {
        particles.current.splice(0, particles.current.length - maxParticles);
      }
    };

    const handleMouseMove = (e) => handleMove(e.clientX, e.clientY, false);
    const handleTouchMove = (e) => {
      if (e.touches.length > 0) {
        handleMove(e.touches[0].clientX, e.touches[0].clientY, true);
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('touchmove', handleTouchMove, { passive: true });

    const render = (time) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Elastic smoothing
      const lerpFactor = 0.18;
      mousePos.current.x += (targetPos.current.x - mousePos.current.x) * lerpFactor;
      mousePos.current.y += (targetPos.current.y - mousePos.current.y) * lerpFactor;

      const { x, y } = mousePos.current;

      // Premium Multi-Layered Glow
      ctx.save();
      ctx.globalCompositeOperation = isLight ? 'source-over' : 'screen';

      // Outer aura
      const auraRadius = isLight ? 45 : 60;
      const aura = ctx.createRadialGradient(x, y, 0, x, y, auraRadius);
      if (isLight) {
        aura.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
        aura.addColorStop(1, 'rgba(59, 130, 246, 0)');
      } else {
        aura.addColorStop(0, 'rgba(0, 210, 255, 0.25)');
        aura.addColorStop(1, 'rgba(0, 210, 255, 0)');
      }
      ctx.fillStyle = aura;
      ctx.beginPath();
      ctx.arc(x, y, auraRadius, 0, Math.PI * 2);
      ctx.fill();

      // Core glow
      const coreRadius = isLight ? 15 : 20;
      const core = ctx.createRadialGradient(x, y, 0, x, y, coreRadius);
      core.addColorStop(0, '#ffffff');
      core.addColorStop(0.4, isLight ? '#3b82f6' : '#00d2ff');
      core.addColorStop(1, 'transparent');
      ctx.fillStyle = core;
      ctx.beginPath();
      ctx.arc(x, y, coreRadius, 0, Math.PI * 2);
      ctx.fill();

      // Inner dot
      ctx.fillStyle = isLight ? '#2563eb' : '#ffffff';
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      // Organic Particles
      for (let i = particles.current.length - 1; i >= 0; i--) {
        const p = particles.current[i];

        // Add slight orbital drift
        p.angle += p.orbit;
        p.vx += Math.cos(p.angle) * 0.1;
        p.vy += Math.sin(p.angle) * 0.1;

        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.015;
        p.size *= 0.97;

        if (p.life <= 0 || p.size < 0.5) {
          particles.current.splice(i, 1);
          continue;
        }

        const shimmer = Math.sin(time * 0.01 + p.shimmer) * 0.2 + 0.8;
        ctx.globalAlpha = p.life * shimmer * 0.8;
        ctx.fillStyle = p.color;

        // Draw glow for each particle
        ctx.shadowBlur = p.size * 2;
        ctx.shadowColor = p.color;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      ctx.globalAlpha = 1.0;
      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchmove', handleTouchMove);
      cancelAnimationFrame(animationFrameId);
      observer.disconnect();
      document.body.classList.remove('custom-cursor-active');
    };
  }, [isLight]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 100000, // Increased to appear above all modals
      }}
    />
  );
}

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
        console.log("🔒 Session expired - Auto logout");
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
          console.log("🔒 Session expired on page load");
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
          console.log("🔒 Session timeout - Auto logout");
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
    const handleBeforeUnload = (e) => {
      const currentToken = localStorage.getItem("token");

      if (currentToken) {
        // Set a flag in sessionStorage to detect if this is a refresh
        const isRefreshing = sessionStorage.getItem("isRefreshing");

        if (!isRefreshing) {
          // This is a tab close or navigation away - clear session
          console.log("🚪 Tab closing - Clearing session");
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
  }, []);

  useEffect(() => {
    localStorage.setItem("lastPage", page);
  }, [page]);

  useEffect(() => {
    if (user && user.email) {
      loadComplaints();
    }
  }, [user]);

  const loadComplaints = async () => {
    if (!user?.email) return;
    try {
      const data = await getAllComplaints(user.email);
      setComplaints(data.complaints || []);
    } catch (error) {
      console.error("Error loading complaints:", error);
      setComplaints([]);
    }
  };

  const handleComplaintSubmit = async (data) => {
    setResult(data);
    await loadComplaints();
    setTimeout(() => {
      navigateTo("profile");
      window.scrollTo(0, 0);
    }, 3000);
  };

  const navigateTo = (newPage) => {
    setPage(newPage);
    if (newPage === "landing") {
      setResult(null);
    }
  };

  const handleLogout = () => {
    console.log("🚪 Logging out user");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("lastPage");
    localStorage.removeItem("sessionTimestamp");
    localStorage.removeItem("lastActivity");
    setUser(null);
    setIsAdminMode(false);
    navigateTo("landing");
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
