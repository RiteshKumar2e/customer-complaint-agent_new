import { useState, useRef, useEffect } from "react";
import api from "../api";
import "../styles/SideChatBot.css";

export default function SideChatBot({ open, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: "agent",
      text:
        "Hi 👋 I’m the AI Support Agent. I can help you understand this website or take your complaint.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const recognitionRef = useRef(null);

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

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("/agent/chat", null, {
        params: { message: input },
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: res.data.response,
          meta: res.data,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "agent", text: "Sorry, I faced an issue. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Function to handle Enter key press
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  };

  return (
    <div className={`side-chat ${open ? "open" : ""}`}>
      <div className="chat-header">
        <span>🤖 AI Agent</span>
        <button onClick={onClose}>✕</button>
      </div>

      <div className="chat-body">
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            <p>{m.text}</p>

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

      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isListening ? "Listening..." : "Type your message..."}
          onKeyDown={handleKeyDown}
          disabled={loading || isListening}
        />
        {voiceSupported && (
          <button
            className={`voice-btn ${isListening ? 'active' : ''}`}
            onClick={toggleVoiceInput}
            title={isListening ? "Stop Listening" : "Voice Search"}
          >
            {isListening ? "🛑" : "🎤"}
          </button>
        )}
        <button onClick={sendMessage} disabled={loading || isListening}>
          {loading ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}