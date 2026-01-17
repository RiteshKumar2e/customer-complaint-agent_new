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
      const count = Math.min(baseCount + Math.floor(speed / 8), 8);

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
  const [isAdminMode, setIsAdminMode] = useState(false);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
    }

    if (window.location.pathname === "/reset-password") {
      setPage("reset-password");
    } else if (window.location.pathname === "/dashboard") {
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
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("lastPage");
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
