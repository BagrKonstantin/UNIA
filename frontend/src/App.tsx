import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './index.css';

// Custom interface for the unilu Assistant 

type Message = {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  id?: string;
  name?: string;
};

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Welcome! I'm your Uni.lu Assistant. I can help with information about the University of Luxembourg, campus services, scheduling, and more. How can I assist you today?" }
  ]);
  const [sessionId] = useState(() => crypto.randomUUID());
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: input
        })
      });

      if (!response.ok) throw new Error("Network response was not ok");

      const data = await response.json();

      if (data.tool_results && data.tool_results.length > 0) {
        setMessages(prev => [
          ...prev,
          ...data.tool_results.map((t: any) => ({ role: 'tool' as const, content: `[Executed Tool] ${t.content}` })),
          { role: 'assistant', content: data.content || "Done! Is there anything else you need?" }
        ]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: data.content }]);
      }

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, the backend seems unavailable. Make sure your Python server is running!" }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-wrapper">
      <header className="header">
        <div className="header-title-container">
          <img src="/logo.png" alt="Uni.lu Logo" className="unilu-logo" />
          <div className="header-title">
            Uni.lu Assistant
          </div>
        </div>
        <div className="status-badge">
          <div className="status-dot"></div>
          Gemma 4 (Local)
        </div>
      </header>

      <div className="chat-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === 'assistant' ? (
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            ) : (
              msg.content
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message assistant" style={{ opacity: 0.7 }}>
            <span style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span className="status-dot" style={{ background: 'var(--accent-unilu-red)' }}></span>
              Thinking...
            </span>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      <form className="input-area" onSubmit={handleSubmit}>
        <input
          type="text"
          className="input-field"
          placeholder="Ask about schedule, campus navigation, University news..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
          autoFocus
        />
        <button type="submit" className="send-btn" disabled={isLoading || !input.trim()}>
          <Send size={22} fill="currentColor" stroke="none" />
        </button>
      </form>
    </div>
  );
}

export default App;
