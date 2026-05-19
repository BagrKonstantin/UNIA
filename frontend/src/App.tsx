import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Square, Calendar, Utensils, Users, GraduationCap, StopCircle } from 'lucide-react';
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

async function convertBlobToWav(blob: Blob): Promise<Blob> {
  const arrayBuffer = await blob.arrayBuffer();
  const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
  
  const numOfChan = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const length = audioBuffer.length * numOfChan * 2;
  const buffer = new ArrayBuffer(44 + length);
  const view = new DataView(buffer);
  
  const writeString = (view: DataView, offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + length, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numOfChan, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numOfChan * 2, true);
  view.setUint16(32, numOfChan * 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, 'data');
  view.setUint32(40, length, true);
  
  const channelData = [];
  for (let i = 0; i < numOfChan; i++) {
    channelData.push(audioBuffer.getChannelData(i));
  }
  
  let offset = 44;
  for (let i = 0; i < audioBuffer.length; i++) {
    for (let channel = 0; channel < numOfChan; channel++) {
      let sample = Math.max(-1, Math.min(1, channelData[channel][i]));
      sample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
      view.setInt16(offset, sample, true);
      offset += 2;
    }
  }
  
  return new Blob([buffer], { type: 'audio/wav' });
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Welcome! I'm your Uni.lu Assistant. I can help with information about the University of Luxembourg, campus services, scheduling, and more. How can I assist you today?" }
  ]);

  const SUGGESTIONS = [
    { label: "Check workshops", query: "What workshops or classes are available today?", icon: <Calendar size={18} /> },
    { label: "Campus Events", query: "Tell me about upcoming events for the week.", icon: <GraduationCap size={18} /> },
    { label: "Canteen Menu", query: "What's on the menu today?", icon: <Utensils size={18} /> },
    { label: "Book a room", query: "Book a room in the library.", icon: <Users size={18} /> },
  ];


  const [sessionId] = useState(() => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    // Fallback for insecure local network connections
    return 'local-' + Math.random().toString(36).substring(2, 9) + Date.now().toString(36);
  });  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!isLoading && !isRecording) {
      inputRef.current?.focus();
    }
  }, [isLoading, isRecording]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    await submitText(input);
  };

  const handleSuggestionClick = async (query: string) => {
    if (isLoading) return;
    await submitText(query);
  };

  const stopGenerating = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      setMessages(prev => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
          newMsgs[newMsgs.length - 1] = { ...lastMsg, isStreaming: false, content: lastMsg.content + " [Generation stopped by user]" };
        }
        return newMsgs;
      });
    }
  };



  const submitText = async (textToSubmit: string) => {
    const userMessage: Message = { role: 'user', content: textToSubmit };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch("http://192.168.178.79:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          session_id: sessionId,
          message: textToSubmit
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

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log("Fetch aborted");
      } else {
        console.error(error);
        setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, the backend seems unavailable. Make sure your Python server is running!" }]);
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };


  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') 
        ? 'audio/webm' 
        : MediaRecorder.isTypeSupported('audio/mp4') 
          ? 'audio/mp4' 
          : '';

      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        try {
          const wavBlob = await convertBlobToWav(audioBlob);
          await handleAudioSubmit(wavBlob);
        } catch (e) {
          console.error("WAV conversion error:", e);
          await handleAudioSubmit(audioBlob);
        }
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleAudioSubmit = async (audioBlob: Blob) => {
    setIsLoading(true);
    setInput("🎙️ Transcribing...");
    
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'audio.wav');
      
      const response = await fetch("http://192.168.178.79:8000/api/transcribe", {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) throw new Error("Transcription failed");
      const data = await response.json();
      
      // Submit the text
      await submitText(data.text);
    } catch (e) {
      console.error("Audio processing error:", e);
      setInput("");
      setIsLoading(false);
    }
  };

  return (
    <div className="app-wrapper">
      <header className="header">
        <div className="header-title-container">
          <img src="/logo.png" alt="Uni.lu Logo" className="unilu-logo" />
          <div className="header-title">
            Luni.U
          </div>
        </div>
        {/*<div className="status-badge">*/}
        {/*  <div className="status-dot"></div>*/}
        {/*  Gemma 4 (Local)*/}
        {/*</div>*/}
      </header>

      <div className="chat-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === 'assistant' ? (
              <div className="assistant-message-content">
                {msg.content ? (
                  <>
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                    {idx === 0 && messages.length === 1 && (
                      <div className="suggestions-container">
                        {SUGGESTIONS.map((suggestion, sIdx) => (
                          <button
                            key={sIdx}
                            className="suggestion-btn"
                            onClick={() => handleSuggestionClick(suggestion.query)}
                          >
                            <span className="suggestion-icon">{suggestion.icon}</span>
                            {suggestion.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </>
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
          ref={inputRef}
          type="text"
          className="input-field"
          placeholder="Ask about schedule, campus navigation, University news..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
          autoFocus
        />
        <button 
          type="button" 
          className={`mic-btn ${isRecording ? 'recording' : ''}`} 
          onClick={toggleRecording}
          disabled={isLoading && !isRecording}
          title={isRecording ? "Stop recording output" : "Start recording"}
        >
          {isRecording ? <Square size={22} fill="currentColor" stroke="none" /> : <Mic size={22} fill="currentColor" stroke="none" />}
        </button>
        {isLoading ? (
          <button type="button" className="stop-btn" onClick={stopGenerating} title="Stop generating">
            <StopCircle size={22} fill="currentColor" stroke="none" />
          </button>
        ) : (
          <button type="submit" className="send-btn" disabled={!input.trim() || isRecording}>
            <Send size={22} fill="currentColor" stroke="none" />
          </button>
        )}
      </form>
    </div>
  );
}

export default App;
