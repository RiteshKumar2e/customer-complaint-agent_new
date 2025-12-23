import { useState } from "react";
import "./../styles/Landing.css";

export default function Landing({ onStart, onDashboard }) {
  const [hoveredFeature, setHoveredFeature] = useState(null);

  const features = [
    {
      id: 1,
      icon: "📊",
      title: "Smart Classification",
      description: "Automatically categorizes complaints into Billing, Technical, Delivery, Service, and Security with high accuracy",
      color: "#22c55e"
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
      color: "#ec4899"
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
      <nav className="landing-navbar">
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
          <a href="#cta" className="nav-link">Contact</a>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="landing-hero">
        <div className="hero-content">
          <div className="badge slide-in-down">
            ✨ Enterprise-Grade AI Solution
          </div>

          <h1 className="hero-title">
            <span className="gradient-text">AI Complaint</span> Resolver
          </h1>
          <p className="hero-subtitle fade-in-up" style={{ animationDelay: "0.2s" }}>
            Revolutionize your customer support with <strong>Quickfix</strong>. Our agentic AI system intelligently classifies, prioritizes, and resolves issues with 98% accuracy, transforming complaints into actionable insights instantly.
          </p>

          <div className="hero-cta-group fade-in-up" style={{ animationDelay: "0.4s" }}>
            <button className="cta-button primary-btn glow-button" onClick={onStart}>
              <span>🚀 Submit Complaint</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>

            <button className="cta-button secondary-btn" onClick={onDashboard}>
              <span>📊 View Dashboard</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 12h18M3 6h18M3 18h18" />
              </svg>
            </button>
          </div>

          <div className="hero-stats fade-in-up" style={{ animationDelay: "0.2s" }}>
            <div className="stat-item">
              <span className="stat-value">6</span>
              <span className="stat-label">AI Agents</span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <span className="stat-value">24/7</span>
              <span className="stat-label">Available</span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <span className="stat-value">98%</span>
              <span className="stat-label">Accuracy</span>
            </div>
          </div>


        </div>
      </div>

      {/* Features Section */}
      <div className="features-section" id="features">
        <div className="features-container">
          <h2 className="section-title">Powered by 6 Specialized AI Agents</h2>
          <p className="section-subtitle">Each agent specializes in a different aspect of complaint resolution</p>

          <div className="features-grid">
            {features.map((feature, index) => (
              <div
                key={feature.id}
                className={`feature-card ${hoveredFeature === feature.id ? 'hovered' : ''}`}
                onMouseEnter={() => setHoveredFeature(feature.id)}
                onMouseLeave={() => setHoveredFeature(null)}
                style={{
                  animationDelay: `${index * 0.1}s`,
                  '--feature-color': feature.color
                }}
              >
                <div className="feature-icon">{feature.icon}</div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
                <div className="feature-bar"></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="stats-section" id="stats">
        <div className="stats-container">
          <h2 className="section-title">Why Choose Quickfix</h2>

          <div className="benefits-grid">
            <div className="benefit-card">
              <div className="benefit-icon">⚡</div>
              <h3>Lightning Fast</h3>
              <p>Complaints processed in seconds, not hours</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">🎯</div>
              <h3>Highly Accurate</h3>
              <p>98% classification accuracy with ML models</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">🔒</div>
              <h3>Secure</h3>
              <p>Enterprise-grade security for your data</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">📈</div>
              <h3>Scalable</h3>
              <p>Handles unlimited complaints efficiently</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">🤝</div>
              <h3>Human Support</h3>
              <p>Escalates complex issues to experts</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">📊</div>
              <h3>Analytics</h3>
              <p>Real-time insights and reporting</p>
            </div>
          </div>

          <div className="stats-boxes" id="cta">
            <div className="stat-card premium">
              <div className="stat-number">6</div>
              <p>Specialized<br />AI Agents</p>
            </div>
            <div className="stat-card premium">
              <div className="stat-number">5</div>
              <p>Complaint<br />Categories</p>
            </div>
            <div className="stat-card premium">
              <div className="stat-number">3</div>
              <p>Priority<br />Levels</p>
            </div>
            <div className="stat-card premium">
              <div className="stat-number">100%</div>
              <p>Uptime<br />Guaranteed</p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="final-cta-section">
        <div className="final-cta-content">
          <h2>Ready to Transform Your Customer Support?</h2>
          <p>Join thousands of businesses using AI-powered complaint resolution</p>
          <button className="cta-button primary-btn glow-button large" onClick={onStart}>
            Get Started Now
          </button>
        </div>
      </div>

      {/* Footer Section */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-section">
            <h4>About Quickfix</h4>
            <p>
              Enterprise-grade agentic AI platform for intelligent complaint
              classification, prioritization, automated responses, and smart
              escalation.
            </p>
          </div>

          <div className="footer-section">
            <h4>Quick Links</h4>
            <ul>
              <li><a href="#features">Features</a></li>
              <li><a href="#about">About</a></li>
              <li><a href="#contact">Contact</a></li>
              <li>
                <a
                  href="https://github.com/RiteshKumar2e"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  GitHub
                </a>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>Contact Information</h4>
            <div className="contact-info">
              <p>
                <span className="contact-icon">📧</span>
                <a href="mailto:riteshkumar90359@gmail.com">
                  riteshkumar90359@gmail.com
                </a>
              </p>
              <p>
                <span className="contact-icon">📱</span>
                <a href="tel:+916206269895">+91 62062 69895</a>
              </p>
              <p>
                <span className="contact-icon">🐙</span>
                <a
                  href="https://github.com/RiteshKumar2e"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  github.com/RiteshKumar2e
                </a>
              </p>
            </div>
          </div>

          <div className="footer-section">
            <h4>Connect</h4>
            <div className="social-links">
              <a
                href="https://www.linkedin.com/in/ritesh-kumar-b3a654253"
                target="_blank"
                rel="noopener noreferrer"
                className="social-icon"
                title="LinkedIn"
              >
                in
              </a>
              <a
                href="https://github.com/RiteshKumar2e"
                target="_blank"
                rel="noopener noreferrer"
                className="social-icon"
                title="GitHub"
              >
                ⭐
              </a>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2025 Quickfix. All rights reserved.</p>
          <div className="footer-links">
            <a href="#">Privacy Policy</a>
            <span className="separator">|</span>
            <a href="#">Terms of Service</a>
            <span className="separator">|</span>
            <a href="#">Cookie Policy</a>
          </div>
        </div>
      </footer>
    </section>
  );
}
