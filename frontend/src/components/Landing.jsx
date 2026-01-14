import { useState, useEffect, useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Points, PointMaterial, Stars } from "@react-three/drei";
import * as random from "maath/random/dist/maath-random.esm";
import "./../styles/Landing.css";
import CookieConsent from "./CookieConsent";
import ThemeToggle from "./ThemeToggle";

// --- Internal 3D Components (Conditional Dark Mode) ---
function ParticleGlobe() {
  const ref = useRef();
  const [sphere] = useState(() => random.inSphere(new Float32Array(3000), { radius: 1.5 }));

  useFrame((state, delta) => {
    ref.current.rotation.x -= delta / 15;
    ref.current.rotation.y -= delta / 20;
  });

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={sphere} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color="#818cf8"
          size={0.005}
          sizeAttenuation={true}
          depthWrite={false}
          blending={1}
        />
      </Points>
    </group>
  );
}

function FloatingGeometry() {
  const group = useRef();
  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    group.current.rotation.y = Math.sin(time / 4) / 4;
    group.current.rotation.x = Math.cos(time / 4) / 4;
  });

  return (
    <group ref={group}>
      <mesh position={[-1.2, 0.5, -0.5]}>
        <icosahedronGeometry args={[0.2, 1]} />
        <meshStandardMaterial color="#6366f1" wireframe transparent opacity={0.15} />
      </mesh>
      <mesh position={[1.2, -0.5, -0.5]}>
        <icosahedronGeometry args={[0.25, 1]} />
        <meshStandardMaterial color="#818cf8" wireframe transparent opacity={0.15} />
      </mesh>
    </group>
  );
}

function HeroBackground() {
  const [isLight, setIsLight] = useState(() => document.body.classList.contains('light-theme'));

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsLight(document.body.classList.contains('light-theme'));
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  // Return null if light theme to keep it "as usual"
  if (isLight) return null;

  return (
    <div className="three-bg-overlay-landing">
      <Canvas camera={{ position: [0, 0, 1.2] }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <Stars radius={100} depth={50} count={4000} factor={4} saturation={0} fade speed={1} />
        <ParticleGlobe />
        <FloatingGeometry />
      </Canvas>
    </div>
  );
}

// ----------------------------------------------------

export default function Landing({ user, onStart, onAdminLogin, onDashboard }) {
  const [hoveredFeature, setHoveredFeature] = useState(null);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [activeModal, setActiveModal] = useState(null); // 'privacy' or 'terms'
  const [activeFaq, setActiveFaq] = useState(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // AI Voice Introduction Logic (Expanded Hinglish Version)
  useEffect(() => {
    const introText = "Welcome to Quickfix AI! Main aapka digital neural guide hoon. Yeh ek powerful multi-agent ecosystem hai jo aapki complaints ko smartly prioritize karta hai. Explore kijiye Quickfix AI ko, jahan technology aur empathy milkar customer support transform karte hain.";

    const speakIntro = () => {
      if (sessionStorage.getItem('intro_spoken')) return;

      const synth = window.speechSynthesis;
      if (!synth) return;

      synth.cancel();

      const utterance = new SpeechSynthesisUtterance(introText);

      // Try to find a Hindi or Indian English voice for natural Hinglish flow
      const voices = synth.getVoices();
      const preferredVoice = voices.find(v =>
        v.lang.includes('hi-IN') ||
        v.lang.includes('en-IN') ||
        v.name.includes('India') ||
        v.name.includes('Google hi-IN')
      );

      if (preferredVoice) {
        utterance.voice = preferredVoice;
        utterance.lang = preferredVoice.lang;
      } else {
        utterance.lang = 'hi-IN'; // Fallback to Hindi lang code
      }

      utterance.rate = 1.0;
      utterance.pitch = 1.1; // Slightly higher pitch for a friendly assistant tone

      utterance.onend = () => {
        sessionStorage.setItem('intro_spoken', 'true');
      };

      synth.speak(utterance);
    };

    // Browsers often block auto-speech without interaction. 
    // We try immediately, but also add a one-time click listener as a fallback.
    const timer = setTimeout(speakIntro, 1000);

    const handleFirstInteraction = () => {
      speakIntro();
      window.removeEventListener('click', handleFirstInteraction);
      window.removeEventListener('scroll', handleFirstInteraction);
    };

    window.addEventListener('click', handleFirstInteraction);
    window.addEventListener('scroll', handleFirstInteraction);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('click', handleFirstInteraction);
      window.removeEventListener('scroll', handleFirstInteraction);
    };
  }, []);


  // Scroll to Top Logic
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const features = [
    {
      icon: "📊",
      title: "Smart Classification",
      description: "Automatically categorizes complaints into Billing, Technical, Delivery, Service, and Security with high accuracy.",
      color: "#667eea"
    },
    {
      icon: "⚡",
      title: "Priority Detection",
      description: "Instantly identifies urgent issues and escalates critical complaints to human support immediately.",
      color: "#22c55e"
    },
    {
      icon: "😊",
      title: "Sentiment Analysis",
      description: "Analyzes customer emotions to gauge satisfaction levels and emotional context accurately.",
      color: "#ec4899"
    },
    {
      icon: "💡",
      title: "Solution Suggestions",
      description: "Generates intelligent, actionable solutions tailored to each unique complaint type and context.",
      color: "#3b82f6"
    },
    {
      icon: "🎯",
      title: "Satisfaction Prediction",
      description: "Predicts customer satisfaction with proposed resolutions using advanced ML algorithms.",
      color: "#764ba2"
    },
    {
      icon: "🔍",
      title: "Pattern Recognition",
      description: "Finds similar past complaints to ensure consistent and reliable handling of issues.",
      color: "#14b8a6"
    }
  ];

  const faqs = [
    {
      question: "How does the multi-agent system work?",
      answer: "Quickfix uses a specialized cluster of AI agents. Each agent handles a specific task—like sentiment analysis or classification—and they cross-communicate to ensure the final resolution is accurate and context-aware."
    },
    {
      question: "Is my data secure?",
      answer: "Absolutely. We use enterprise-grade AES-256 encryption for all data at rest and in transit. Your complaints and customer details are never used for training public models."
    },
    {
      question: "Can I integrate this with my existing CRM?",
      answer: "Yes, Quickfix is designed with an API-first approach, allowing seamless integration with popular CRMs like Salesforce, HubSpot, and Zendesk."
    },
    {
      question: "What is the accuracy rate of the AI?",
      answer: "Currently, our agentic orchestration performs with a 98% surgical precision in classification and a 95% success rate in suggested resolutions."
    }
  ];

  return (
    <div className="landing-container">
      <HeroBackground />
      {/* Background Effects */}

      {/* Header */}
      <header className={`landing-header ${isMenuOpen ? 'menu-open' : ''}`}>
        <div className="header-left">
          <div className="navbar-brand ecohealth-logo" onClick={scrollToTop}>
            <div className="logo-orb">
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="18" cy="18" r="18" fill="url(#orb-grad)" fillOpacity="0.15" />
                <circle cx="18" cy="18" r="17.5" stroke="url(#orb-grad)" strokeOpacity="0.2" />
                <path d="M18 8L10 12V18C10 23.41 13.41 28.47 18 30C22.59 28.47 26 23.41 26 18V12L18 8Z" fill="url(#shield-grad)" />
                <path d="M18 13V17M18 21H18.01" stroke="white" strokeWidth="2" strokeLinecap="round" />
                <defs>
                  <linearGradient id="orb-grad" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#7c9aff" />
                    <stop offset="1" stopColor="#b69eff" />
                  </linearGradient>
                  <linearGradient id="shield-grad" x1="10" y1="8" x2="26" y2="30" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#7c9aff" />
                    <stop offset="1" stopColor="#3b82f6" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div className="brand-text-stack">
              <span className="logo-text">Quickfix</span>
            </div>
          </div>
        </div>

        <nav className={`nav-links ${isMenuOpen ? 'is-open' : ''}`}>
          <div className="mobile-auth-buttons">
            <button className="btn-admin" onClick={() => { onStart(); setIsMenuOpen(false); }}>
              {user?.role === "Admin" ? "Admin Dash" : (user ? "Dashboard" : "Sign In")}
            </button>
            {!user && (
              <button className="btn-admin admin-special" onClick={() => { onAdminLogin(); setIsMenuOpen(false); }} style={{ marginTop: '10px', background: 'var(--secondary)' }}>
                Admin Login
              </button>
            )}
          </div>
          <button onClick={() => { scrollToTop(); setIsMenuOpen(false); }} className="nav-btn-home">Home</button>
          <button onClick={() => { scrollToSection('mission'); setIsMenuOpen(false); }}>Mission</button>
          <button onClick={() => { scrollToSection('features'); setIsMenuOpen(false); }}>About</button>
          <button onClick={() => { scrollToSection('goals'); setIsMenuOpen(false); }}>Goals</button>
          <button onClick={() => { scrollToSection('team'); setIsMenuOpen(false); }}>Team</button>
          <button onClick={() => { scrollToSection('testimonials'); setIsMenuOpen(false); }}>Testimonials</button>
          <button onClick={() => { scrollToSection('contact'); setIsMenuOpen(false); }}>Contact</button>
        </nav>

        <div className="header-right">
          <div className="header-actions">
            <ThemeToggle className="navbar-theme-toggle" />
            <button className="mobile-menu-toggle" onClick={() => setIsMenuOpen(!isMenuOpen)}>
              <span className={`hamburger ${isMenuOpen ? 'active' : ''}`}></span>
            </button>
          </div>
          <div className="auth-buttons">
            <button className="btn-admin" onClick={onStart}>
              {user?.role === "Admin" ? `Admin Panel` : (user ? `Dashboard` : "Sign In")}
            </button>
            {!user && (
              <button className="btn-admin admin-special" onClick={onAdminLogin}>
                Admin Login
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
          <div className="gradient-orb orb-1" />
          <div className="gradient-orb orb-2" />
          <div className="gradient-orb orb-3" />
        </div>

        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-icon">✨</span>
            <span>AI-Powered Innovation</span>
          </div>

          <h1 className="hero-title">
            Quickfix -AI for Enterprise Support & Multi-Agent Control
          </h1>

          <p className="hero-subtitle">
            Bridging autonomous intelligence and human oversight to create absolute precision and thriving customer success.
          </p>

          <div className="hero-cta">
            {/* Primary Button: Scrolls to demo solutions section */}
            <button className="btn-cta btn-primary" onClick={() => scrollToSection('solutions-demo')}>
              Explore Solutions <span className="arrow">→</span>
            </button>

            {/* Secondary Button: Scrolls to features section using ID */}
            <button className="btn-secondary" onClick={() => scrollToSection('features')}>
              Learn More
            </button>
          </div>

          <div className="features-grid-mini">
            <div className="feature-mini">
              <span className="icon">🧠</span>
              <span>Recursive Reasoning</span>
            </div>
            <div className="feature-mini">
              <span className="icon">🛡️</span>
              <span>Kernel Security</span>
            </div>
            <div className="feature-mini">
              <span className="icon">📈</span>
              <span>Predictive Resolve</span>
            </div>
            <div className="feature-mini">
              <span className="icon">⚡</span>
              <span>Atomic Latency</span>
            </div>
          </div>
        </div>


      </section>

      {/* Vision & Mission Section */}
      <section className="vision-mission-section" id="mission">
        <div className="container">
          <div className="vision-box" data-aos="fade-up">
            <div className="section-tag">Our Vision</div>
            <h2 className="vision-text">
              To redefine the global standard of customer success through autonomous AI intelligence.
            </h2>
          </div>

          <div className="mission-content">
            <div className="mission-card" data-aos="fade-right">
              <div className="section-tag">Our Mission</div>
              <h3 className="mission-title">Empowering Enterprises with Agentic Precision</h3>
              <p className="mission-description">
                Our mission is to bridge the gap between complex technical logic and human-centric service.
                We deploy high-frequency agentic clusters that analyze, classify, and resolve issues with
                surgical precision. By combining emotional intelligence with recursive reasoning, we ensure
                that every customer feels heard, valued, and satisfied in real-time, reducing resolution
                cycles from days to mere seconds.
              </p>
              <div className="mission-stats">
                <div className="stat-item">
                  <span className="stat-value">98%</span>
                  <span className="stat-label">Surgical Accuracy</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">&lt; 2s</span>
                  <span className="stat-label">Response Latency</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="solutions-section" id="features">
        <div className="section-header">
          <h2 className="section-title">About <span>Quickfix</span></h2>
          <p className="section-subtitle">Six specialized agents working in high-frequency synchronization.</p>
        </div>

        <div className="solutions-grid">
          {features.map((feature, index) => (
            <div
              key={index}
              className="solution-card"
              onMouseEnter={() => setHoveredFeature(index)}
              onMouseLeave={() => setHoveredFeature(null)}
              onMouseMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                e.currentTarget.style.setProperty('--mouse-x', `${x}px`);
                e.currentTarget.style.setProperty('--mouse-y', `${y}px`);
              }}
            >
              <div className="card-glow" />
              <div
                className="solution-icon"
                style={{ background: feature.color }}
              >
                <span className="icon-text">{feature.icon}</span>
              </div>
              <h3 className="solution-title">{feature.title}</h3>
              <p className="solution-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Strategic Goals Section */}
      <section className="goals-section" id="goals">
        <div className="section-header">
          <h2 className="section-title">Strategic <span>Goals</span></h2>
          <p className="section-subtitle">Our mission: Redefining the future of autonomous support.</p>
        </div>
        <div className="goals-grid">
          {[
            {
              title: "Absolute Efficiency",
              desc: "Reducing resolution cycles from days to seconds using high-frequency agentic reasoning.",
              icon: "🚀",
              metric: "< 2s Response"
            },
            {
              title: "User Empowerment",
              desc: "Giving every user a transparent, AI-backed voice that ensures fair and consistent resolution.",
              icon: "⚖️",
              metric: "100% Transparency"
            },
            {
              title: "Emotional Resonance",
              desc: "Deploying sentiment-aware agents that understand the human context behind every complaint.",
              icon: "🧠",
              metric: "99% Empathy Rate"
            },
            {
              title: "Seamless Scaling",
              desc: "Architecture designed to handle millions of concurrent resolutions without degradation.",
              icon: "📈",
              metric: "Infinite Scale"
            }
          ].map((goal, idx) => (
            <div key={idx} className="goal-card">
              <div className="goal-icon-wrapper">
                <span className="goal-icon">{goal.icon}</span>
              </div>
              <div className="goal-content">
                <h3>{goal.title}</h3>
                <p>{goal.desc}</p>
                <div className="goal-metric">
                  <span className="metric-dot"></span>
                  <span className="metric-text">{goal.metric}</span>
                </div>
              </div>
              <div className="goal-card-bg"></div>
            </div>
          ))}
        </div>
      </section>

      {/* Demo Solutions / Use Cases Section */}
      <section className="demo-section" id="solutions-demo">
        <div className="section-header">
          <h2 className="section-title">Intelligence <span>In Action</span></h2>
          <p className="section-subtitle">Real-world scenarios handled by our multi-agent architecture.</p>
        </div>

        <div className="demo-container">
          {[
            {
              type: "Billing",
              case: "Unexpected Overcharge",
              process: "Agent identifies billing error → Cross-references history → Generates refund proposal → Alerts Team.",
              impact: "Reduction in resolution time",
              icon: "💳",
              color: "rgba(99, 102, 241, 0.15)"
            },
            {
              type: "Technical",
              case: "System Latency Issue",
              process: "Monitors logs → Classifies root cause → Provides troubleshooting steps → Predicts fix probability.",
              impact: "Approx surgical accuracy",
              icon: "⚙️",
              color: "rgba(34, 197, 94, 0.15)"
            },
            {
              type: "Security",
              case: "Suspicious Login Attempt",
              process: "Detects anomaly → Triggers immediate lockdown → Notifies security agents → Initiates identity verification.",
              impact: "Real-time threat mitigation",
              icon: "🛡️",
              color: "rgba(239, 68, 68, 0.15)"
            }
          ].map((demo, idx) => (
            <div key={idx} className="demo-scenario-card" style={{ '--demo-accent': demo.color }}>
              <div className="demo-card-head">
                <span className="demo-type-badge">{demo.type}</span>
                <span className="demo-icon-mini">{demo.icon}</span>
              </div>
              <h4>{demo.case}</h4>
              <div className="demo-process-line">
                <p>{demo.process}</p>
              </div>
              <div className="demo-impact-footer">
                <span className="impact-label">Impact:</span>
                <span className="impact-value">{demo.impact}</span>
              </div>
            </div>
          ))}
        </div>

      </section>




      {/* Team Section */}
      <section className="about-section" id="team">
        <div className="section-header">
          <h2 className="section-title">The <span>Architect</span></h2>
          <p className="section-subtitle">Pioneering the intersection of Full-Stack and AI intelligence.</p>
        </div>
        <div className="about-content">
          <div className="solution-card team-card-primary">
            <div className="solution-icon team-avatar-icon">
              <span className="icon-text">👨‍💻</span>
            </div>
            <h3 className="solution-title team-name">Ritesh Kumar</h3>
            <p className="team-role-pill">Software Engineer | AI & ML Enthusiast</p>
            <p className="solution-description team-bio">
              AI & ML | Experienced in React, SQL |
              Passionate about AI, ML, and full-stack development.
            </p>
            <div className="social-links-premium1">
              <a href="https://www.linkedin.com/in/ritesh-kumar-b3a654253" target="_blank" rel="noopener noreferrer" title="LinkedIn">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.238 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" /></svg>
              </a>
              <a href="https://github.com/RiteshKumar2e" target="_blank" rel="noopener noreferrer" title="GitHub">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="testimonials-section" id="testimonials">
        <div className="section-header">
          <h2 className="section-title">Client <span>Feedback</span></h2>
          <p className="section-subtitle">What industry leaders are saying about Quickfix AI.</p>
        </div>
        <div className="testimonials-grid">
          {[
            {
              name: "S. Johnson",
              role: "Operations Head",
              text: "The AI agent clusters have reduced our resolution cycles from hours to seconds. A scalable solution for enterprise-level support.",
              rating: 5
            },
            {
              name: "M. Chen",
              role: "Support Director",
              text: "Surgical precision in classification. The sentiment-aware routing ensures our high-priority tickets reach the right team instantly.",
              rating: 5
            },
            {
              name: "E. Rodriguez",
              role: "Tech Lead",
              text: "Seamless API integration and enterprise-grade security. Quickfix is the benchmark for autonomous customer success systems.",
              rating: 5
            }
          ].map((testimonial, idx) => (
            <div key={idx} className="testimonial-card">
              <div className="testimonial-header">
                <div className="testimonial-id-badge">
                  <span>{testimonial.name.charAt(0)}</span>
                </div>
                <div className="testimonial-info">
                  <h4>{testimonial.name}</h4>
                  <p className="testimonial-role">{testimonial.role}</p>
                </div>
              </div>
              <div className="rating-stars">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <span key={i} className="star">★</span>
                ))}
              </div>
              <p className="testimonial-text">{testimonial.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ Section */}
      <section className="faq-section">
        <div className="section-header">
          <h2 className="section-title">Common <span>Questions</span></h2>
          <p className="section-subtitle">Everything you need to know about our intelligence.</p>
        </div>
        <div className="faq-grid">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className={`faq-item ${activeFaq === index ? 'active' : ''}`}
              onClick={() => setActiveFaq(activeFaq === index ? null : index)}
            >
              <div className="faq-question">
                <h3>{faq.question}</h3>
                <span className="faq-toggle">{activeFaq === index ? '−' : '+'}</span>
              </div>
              <div className="faq-answer">
                <p>{faq.answer}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <footer className="footer" id="contact">
        <div className="footer-content">
          <div className="footer-section brand-info">
            <div className="navbar-brand ecohealth-logo" onClick={scrollToTop} style={{ marginBottom: '1.5rem', padding: 0 }}>
              <div className="logo-orb" style={{ width: '36px', height: '36px' }}>
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="18" cy="18" r="18" fill="url(#footer-orb-grad)" fillOpacity="0.15" />
                  <path d="M18 8L10 12V18C10 23.41 13.41 28.47 18 30C22.59 28.47 26 23.41 26 18V12L18 8Z" fill="url(#footer-shield-grad)" />
                  <defs>
                    <linearGradient id="footer-orb-grad" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#6366f1" />
                      <stop offset="1" stopColor="#818cf8" />
                    </linearGradient>
                    <linearGradient id="footer-shield-grad" x1="10" y1="8" x2="26" y2="30" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#6366f1" />
                      <stop offset="1" stopColor="#4f46e5" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <span className="logo-text">Quickfix</span>
            </div>
            <h3 className="connect-title">Connect With Us</h3>
            <div className="social-links-premium2">
              <a href="https://github.com/RiteshKumar2e" target="_blank" rel="noopener noreferrer" title="GitHub">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg>
              </a>
              <a href="https://www.linkedin.com/in/ritesh-kumar-b3a654253" target="_blank" rel="noopener noreferrer" title="LinkedIn">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.238 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" /></svg>
              </a>
              <a href="mailto:riteshkumar90359@gmail.com" title="Email">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
              </a>
            </div>
          </div>
          <div className="footer-section">
            <h4>Ecosystem</h4>
            <button onClick={() => scrollToSection('features')} className="footer-btn">Neural Grid</button>
            <button onClick={() => scrollToSection('team')} className="footer-btn">The Team</button>
            <button onClick={() => window.open('https://github.com/RiteshKumar2e', '_blank')} className="footer-btn">Dev Source</button>
          </div>
          <div className="footer-section">
            <h4>Direct Contact</h4>
            <p>📧 riteshkumar90359@gmail.com</p>
          </div>
          <div className="footer-section">
            <h4>Legal</h4>
            <button onClick={() => setActiveModal('privacy')} className="footer-btn">Privacy Policy</button>
            <button onClick={() => setActiveModal('terms')} className="footer-btn">Terms of Service</button>
            <button onClick={() => setActiveModal('cookie')} className="footer-btn">Cookie Policy</button>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2025 Quickfix. Powered by Agentic Reasoning Clusters.</p>
        </div>
      </footer>

      {/* Modal Components */}
      {
        activeModal && (
          <div className="modal-overlay" onClick={() => setActiveModal(null)}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
              <button className="modal-close" onClick={() => setActiveModal(null)}>&times;</button>

              {activeModal === 'privacy' && (
                <div className="modal-body">
                  <h2>Privacy Policy</h2>
                  <p className="last-updated">Last Updated: October 12, 2025</p>
                  <section>
                    <h3>1. Information We Collect</h3>
                    <p>We collect information you provide directly to us, including name, email address, and any other information you choose to provide through our contact forms or process clusters.</p>
                  </section>
                  <section>
                    <h3>2. How We Use Your Information</h3>
                    <ul>
                      <li>To provide, maintain, and improve our agentic services</li>
                      <li>To communicate with you about support resolutions</li>
                      <li>To monitor and analyze architectural trends and usage</li>
                      <li>To detect, prevent, and address technical issues</li>
                    </ul>
                  </section>
                  <section>
                    <h3>3. Data Security</h3>
                    <p>We implement appropriate technical and organizational measures to protect your agentic data against unauthorized access, alteration, disclosure, or destruction.</p>
                  </section>
                  <section>
                    <h3>4. Your Rights</h3>
                    <p>You have the right to access, update, or delete your personal information. Contact us at riteshkumar90359@gmail.com for any privacy-related requests.</p>
                  </section>
                  <button className="btn-primary" onClick={() => setActiveModal(null)} style={{ marginTop: '2rem', width: '100%' }}>I Understand</button>
                </div>
              )}

              {activeModal === 'terms' && (
                <div className="modal-body">
                  <h2>Terms of Service</h2>
                  <p className="last-updated">Last Updated: October 12, 2025</p>
                  <section>
                    <h3>1. Acceptance of Terms</h3>
                    <p>By accessing and using Quickfix AI's services, you accept and agree to be bound by these Terms of Service.</p>
                  </section>
                  <section>
                    <h3>2. Use of Services</h3>
                    <p>You agree to use our services only for lawful purposes and in accordance with these Terms. You must not:</p>
                    <ul>
                      <li>Violate any applicable laws or regulations</li>
                      <li>Infringe upon the architecture rights of others</li>
                      <li>Transmit any harmful or malicious code</li>
                      <li>Attempt to gain unauthorized access to our neural systems</li>
                    </ul>
                  </section>
                  <section>
                    <h3>3. Intellectual Property</h3>
                    <p>All content, features, and functionality of our services are owned by Quickfix AI and protected by international copyright and trade secret laws.</p>
                  </section>
                  <section>
                    <h3>4. Limitation of Liability</h3>
                    <p>Quickfix AI shall not be liable for any indirect, incidental, or consequential damages resulting from your use of our neural support clusters.</p>
                  </section>
                  <button className="btn-primary" onClick={() => setActiveModal(null)} style={{ marginTop: '2rem', width: '100%' }}>I Understand</button>
                </div>
              )}

              {activeModal === 'cookie' && (
                <div className="modal-body">
                  <h2>Cookie Policy</h2>
                  <p className="last-updated">Last Updated: October 12, 2025</p>
                  <section>
                    <h3>1. What are Cookies?</h3>
                    <p>Cookies are small text files stored on your device that help us improve your experience and understand how our agentic platform is used.</p>
                  </section>
                  <section>
                    <h3>2. How We Use Cookies</h3>
                    <ul>
                      <li><strong>Essential:</strong> Required for the platform to function securely.</li>
                      <li><strong>Performance:</strong> Help us measure how agents interact with the interface.</li>
                      <li><strong>Functionality:</strong> Remember your preferences and dashboard layout.</li>
                    </ul>
                  </section>
                  <section>
                    <h3>3. Managing Cookies</h3>
                    <p>Most browsers allow you to control cookies through their settings. However, disabling essential cookies may impact the performance of our neural resolution clusters.</p>
                  </section>
                  <button className="btn-primary" onClick={() => setActiveModal(null)} style={{ marginTop: '2rem', width: '100%' }}>I Understand</button>
                </div>
              )}
            </div>
          </div>
        )
      }

      {/* Scroll to Top */}
      {
        showScrollTop && (
          <button className="scroll-to-top" onClick={scrollToTop}>
            <span>↑</span>
          </button>
        )
      }

      {/* Cookie Consent Banner */}
      <CookieConsent />
    </div >
  );
}
