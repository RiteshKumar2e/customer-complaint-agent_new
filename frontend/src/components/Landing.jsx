import { useState, useEffect } from "react";
import "./../styles/Landing.css";

export default function Landing({ onStart, onDashboard, onFeedback }) {
  const [hoveredFeature, setHoveredFeature] = useState(null);
  const [scrolled, setScrolled] = useState(false);

  // Handle Navbar Scroll Effect
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const features = [
    {
      id: 1,
      icon: "📊",
      title: "Smart Classification",
      description: "Automatically categorizes complaints into Billing, Technical, Delivery, Service, and Security with high accuracy",
      color: "#10b981"
    },
    {
      id: 2,
      icon: "⚡",
      title: "Priority Detection",
      description: "Instantly identifies urgent issues and escalates critical complaints to human support immediately",
      color: "#f59e0b"
    },
    {
      id: 3,
      icon: "😊",
      title: "Sentiment Analysis",
      description: "Analyzes customer emotions to gauge satisfaction levels and emotional context accurately",
      color: "#6366f1"
    },
    {
      id: 4,
      icon: "💡",
      title: "Solution Suggestions",
      description: "Generates intelligent, actionable solutions tailored to each unique complaint type and context",
      color: "#3b82f6"
    },
    {
      id: 5,
      icon: "🎯",
      title: "Satisfaction Prediction",
      description: "Predicts customer satisfaction with proposed resolutions using advanced ML algorithms",
      color: "#8b5cf6"
    },
    {
      id: 6,
      icon: "🔍",
      title: "Pattern Recognition",
      description: "Finds similar past complaints to ensure consistent and reliable handling of issues",
      color: "#06b6d4"
    }
  ];

  return (
    <section className="landing">
      <div className="overlay" />
      <div className="animated-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>

      {/* Navigation Bar */}
      <nav className={`landing-navbar ${scrolled ? "scrolled" : ""}`}>
        <div className="navbar-brand">
          <span className="logo-icon agent-logo">
            <span className="agent-core"></span>
            <span className="agent-ring"></span>
          </span>
          <span className="logo-text">Quickfix</span>
        </div>

        <div className="navbar-links">
          <a href="#features" className="nav-link">Features</a>
          <a href="#stats" className="nav-link">About</a>
          <button
            onClick={onFeedback}
            className="nav-link feedback-trigger"
          >
            Feedback
          </button>
          <button className="nav-cta" onClick={onStart}>Get Started</button>
        </div>
      </nav>

      {/* Hero Section Container */}
      <div className="hero-section-wrapper">
        <div className="landing-hero">
          <div className="hero-content">
            <div className="badge slide-in-down">
              <span className="pulse-dot"></span>
              ✨ v2.0 Enterprise Solution
            </div>

            <h1 className="hero-title">
              <span className="gradient-text">Agentic AI</span> for Support
            </h1>
            <p className="hero-subtitle fade-in-up">
              The world's first multi-agent system designed to resolve customer complaints with absolute precision.
              <strong> 98% resolution accuracy</strong>, delivered in milliseconds.
            </p>

            <div className="hero-cta-group fade-in-up">
              <button className="cta-button primary-btn" onClick={onStart}>
                <span>Launch Agent</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>

              <button className="cta-button secondary-btn" onClick={onDashboard}>
                <span>Live Demo</span>
              </button>
            </div>

            <div className="hero-stats-row">
              <div className="hero-stat-box">
                <span className="val">6</span>
                <span className="lab">Agents</span>
              </div>
              <div className="hero-stat-box">
                <span className="val">24/7</span>
                <span className="lab">Active</span>
              </div>
              <div className="hero-stat-box">
                <span className="val">&lt;2s</span>
                <span className="lab">Speed</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="features-section" id="features">
        <div className="features-container">
          <div className="section-header">
            <h2 className="section-title">The Multi-Agent Ecosystem</h2>
            <p className="section-subtitle">Six specialized neural agents working in synergy to orchestrate the perfect resolution path.</p>
          </div>

          <div className="features-grid">
            {features.map((feature, index) => (
              <div
                key={feature.id}
                className={`feature-card ${hoveredFeature === feature.id ? 'hovered' : ''}`}
                onMouseEnter={() => setHoveredFeature(feature.id)}
                onMouseLeave={() => setHoveredFeature(null)}
                style={{
                  '--feature-color': feature.color,
                  animationDelay: `${index * 0.1}s`
                }}
              >
                <div className="feature-icon-wrapper">
                  <div className="feature-icon">{feature.icon}</div>
                </div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
                <div className="feature-status">
                  <span className="status-dot"></span>
                  Operational
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Benefits Section */}
      <div className="stats-section" id="stats">
        <div className="stats-container">
          <div className="section-header">
            <h2 className="section-title">Engineered for Performance</h2>
            <p className="section-subtitle">Scale your support operations without compromising on quality or emotional intelligence.</p>
          </div>

          <div className="benefits-grid">
            <div className="benefit-card">
              <div className="benefit-icon">⚡</div>
              <h3>Ultra-low Latency</h3>
              <p>Proprietary inference engines ensure response times under 2 seconds for any complexity.</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">🎯</div>
              <h3>Precision Logic</h3>
              <p>Zero-shot classification combined with few-shot reasoning for surgical accuracy.</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">🔒</div>
              <h3>Vault Security</h3>
              <p>SOC2 Type II compliant pipelines with end-to-end encryption for all customer data.</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">📈</div>
              <h3>Auto-scaling</h3>
              <p>Kubernetes-backed infrastructure that scales to millions of requests without manual tuning.</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">🤝</div>
              <h3>Smart Handoff</h3>
              <p>Intelligent agent-to-human escalation that preserves full context and sentiment history.</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">📊</div>
              <h3>Neural Insights</h3>
              <p>Vector-based pattern recognition to identify systemic product issues before they trend.</p>
            </div>
          </div>

          <div className="stats-boxes">
            <div className="stat-card premium">
              <div className="stat-number">98%</div>
              <p>Sentiment Analysis<br />Accuracy</p>
            </div>
            <div className="stat-card premium">
              <div className="stat-number">10x</div>
              <p>Reduced Ops<br />Overhead</p>
            </div>
            <div className="stat-card premium">
              <div className="stat-number">O(log n)</div>
              <p>Predictive<br />Complexity</p>
            </div>
            <div className="stat-card premium">
              <div className="stat-number">256-bit</div>
              <p>State-of-the-art<br />Encryption</p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="final-cta-section" id="cta">
        <div className="cta-glow-bg"></div>
        <div className="final-cta-content">
          <div className="cta-badge">Ready to Scale?</div>
          <h2>Join the Future of Support</h2>
          <p>Experience the power of the Quickfix multi-agent ecosystem today. No credit card required.</p>
          <div className="cta-button-group">
            <button className="cta-button primary-btn large" onClick={onStart}>
              Start Free Trial
            </button>
            <button className="cta-button secondary-btn white large" onClick={onDashboard}>
              Book a Demo
            </button>
          </div>
        </div>
      </div>

      {/* Footer Section */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-section brand-section">
            <div className="navbar-brand">
              <span className="logo-icon agent-logo">
                <span className="agent-core"></span>
                <span className="agent-ring"></span>
              </span>
              <span className="logo-text">Quickfix</span>
            </div>
            <p className="brand-desc">
              Pioneering agentic intelligence to automate complex customer support workflows at scale.
            </p>
            <div className="social-links-minimal">
              <a href="https://linkedin.com" target="_blank" rel="noreferrer">LinkedIn</a>
              <a href="https://github.com/RiteshKumar2e" target="_blank" rel="noreferrer">GitHub</a>
              <a href="https://twitter.com" target="_blank" rel="noreferrer">Twitter</a>
            </div>
          </div>

          <div className="footer-section links-section">
            <h4>Product</h4>
            <ul>
              <li><a href="#features">Agent Core</a></li>
              <li><a href="#stats">Intelligence</a></li>
              <li><a href="#cta">Pricing</a></li>
              <li><button onClick={onFeedback} className="footer-link-btn">Feedback</button></li>
            </ul>
          </div>

          <div className="footer-section links-section">
            <h4>Company</h4>
            <ul>
              <li><a href="#">About Us</a></li>
              <li><a href="#">Careers</a></li>
              <li><a href="#">Blog</a></li>
              <li><a href="#">Contact</a></li>
            </ul>
          </div>

          <div className="footer-section subscribe-section">
            <h4>Stay Updated</h4>
            <p>Join our newsletter for the latest AI research.</p>
            <div className="subscribe-form">
              <input type="email" placeholder="email@company.com" />
              <button>Subscribe</button>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <div className="footer-bottom-inner">
            <p>&copy; 2025 Quickfix AI. Built for the modern enterprise.</p>
            <div className="legal-links">
              <a href="#">Privacy</a>
              <a href="#">Terms</a>
              <a href="#">Security</a>
            </div>
          </div>
        </div>
      </footer>
    </section>
  );
}
