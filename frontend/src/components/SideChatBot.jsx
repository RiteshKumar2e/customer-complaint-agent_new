import { useState, useRef, useEffect } from "react";
import api from "../api";
import "../styles/SideChatBot.css";

export default function SideChatBot({ open, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: "agent",
      text:
        "Hi 👋 I'm the AI Support Agent. I can help you understand this website or take your complaint.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const recognitionRef = useRef(null);
  const chatBodyRef = useRef(null);

  // Helper function to format markdown text to HTML
  const formatMessageText = (text) => {
    if (!text) return "";

    let formatted = text;

    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Convert *italic* to <em>
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Convert `code` to <code>
    formatted = formatted.replace(/`(.+?)`/g, '<code>$1</code>');

    // Convert line breaks to <br>
    formatted = formatted.replace(/\n/g, '<br>');

    // Convert numbered lists (1. item)
    formatted = formatted.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="list-item">$1. $2</div>');

    // Convert bullet points (- item or * item)
    formatted = formatted.replace(/^[-*]\s+(.+)$/gm, '<div class="list-item">• $1</div>');

    return formatted;
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages, loading]);

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };

      setVoiceSupported(true);
    }
  }, []);

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const sendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = { role: "user", text: input.trim() };
    const currentInput = input.trim();

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("/agent/chat", { message: currentInput });

      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: res.data.response,
          meta: res.data,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "agent", text: "Sorry, I faced an issue. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`side-chat ${open ? "open" : ""}`}>
      <div className="chat-header">
        <span>🤖 AI Agent</span>
        <button onClick={onClose}>✕</button>
      </div>

      <div className="chat-body" ref={chatBodyRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            <div dangerouslySetInnerHTML={{ __html: formatMessageText(m.text) }} />

            {m.meta && m.meta.type === "complaint" && (
              <div className="chat-meta">
                <span>📂 {m.meta.category}</span>
                <span>⚠ {m.meta.priority}</span>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-msg agent">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
      </div>

      <form className="chat-input" onSubmit={sendMessage}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isListening ? "Listening..." : "Type your message..."}
          disabled={isListening}
          autoComplete="off"
        />
        {voiceSupported && (
          <button
            type="button"
            className={`voice-btn ${isListening ? 'active' : ''}`}
            onClick={toggleVoiceInput}
            title={isListening ? "Stop Listening" : "Voice Search"}
          >
            {isListening ? "🛑" : "🎤"}
          </button>
        )}
        <button type="submit" disabled={loading || !input.trim() || isListening}>
          {loading ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
