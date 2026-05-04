import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './index.css';

// Custom interface for the unilu Assistant 

type Message = {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  id?: string;
  name?: string;
  tools?: string[];
  isStreaming?: boolean;
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

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      
      setMessages(prev => [...prev, { role: 'assistant', content: "", tools: [], isStreaming: true }]);

      let buffer = "";
      while (reader) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        let i;
        while ((i = buffer.indexOf('\n\n')) !== -1) {
          const eventString = buffer.slice(0, i);
          buffer = buffer.slice(i + 2);
          
          if (eventString.startsWith('data: ')) {
            try {
              const dataStr = eventString.slice(6).trim();
              if (!dataStr) continue;
              const data = JSON.parse(dataStr);
              if (data.content) {
                setMessages(prev => {
                  const newMsgs = [...prev];
                  const lastMsg = newMsgs[newMsgs.length - 1];
                  newMsgs[newMsgs.length - 1] = { ...lastMsg, content: lastMsg.content + data.content };
                  return newMsgs;
                });
              } else if (data.tool_call) {
                setMessages(prev => {
                  const newMsgs = [...prev];
                  const lastMsg = newMsgs[newMsgs.length - 1];
                  const tools = lastMsg.tools || [];
                  newMsgs[newMsgs.length - 1] = { ...lastMsg, tools: [...tools, data.tool_call] };
                  return newMsgs;
                });
              }
            } catch (e) {
              console.error("Failed to parse SSE JSON", e, eventString);
            }
          }
        }
      }

      setMessages(prev => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
          newMsgs[newMsgs.length - 1] = { ...lastMsg, isStreaming: false };
        }
        return newMsgs;
      });

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
              <div className="assistant-message-content">
                {msg.content ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  msg.tools && msg.tools.length > 0 ? (
                    <span style={{ display: 'flex', gap: '8px', alignItems: 'center', opacity: 0.7 }}>
                      <span className="status-dot" style={{ background: 'var(--accent-unilu-red)' }}></span>
                      {msg.tools[msg.tools.length - 1]}...
                    </span>
                  ) : msg.isStreaming ? (
                    <span style={{ display: 'flex', gap: '8px', alignItems: 'center', opacity: 0.7 }}>
                      <span className="status-dot" style={{ background: 'var(--accent-unilu-red)' }}></span>
                      Thinking...
                    </span>
                  ) : null
                )}
              </div>
            ) : (
              msg.content
            )}
          </div>
        ))}
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
