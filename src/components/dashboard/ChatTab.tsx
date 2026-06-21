'use client';

import { useState, useRef, useEffect } from 'react';
import type { ChatMessage, PatientInfo } from '@/hooks/useSessions';
import { useVoiceInput } from '@/hooks/useVoiceInput';
import Waveform from './Waveform';

const NLP_API = 'http://localhost:5001';

interface ChatTabProps {
  messages: ChatMessage[];
  onMessagesChange: (msgs: ChatMessage[]) => void;
  patient?: PatientInfo | null;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button className="msg-copy-btn" onClick={handleCopy} title="Copy">
      <span className="material-symbols-outlined">{copied ? 'check' : 'content_copy'}</span>
    </button>
  );
}

export default function ChatTab({ messages, onMessagesChange, patient }: ChatTabProps) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prefixRef = useRef('');
  const wasListeningRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);

  const voice = useVoiceInput({
    onInterim: (text) => setInput(prefixRef.current + text),
    onResult: (text) => { setInput(prefixRef.current + text); prefixRef.current = ''; },
    onError: (err) => console.error('Voice error:', err),
  });

  useEffect(() => {
    if (voice.state === 'listening' && !wasListeningRef.current) {
      prefixRef.current = input ? input + ' ' : '';
      wasListeningRef.current = true;
    }
    if (voice.state === 'idle' && wasListeningRef.current) {
      wasListeningRef.current = false;
    }
  }, [voice.state]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const hasUserMessages = messages.some(m => m.role === 'user');

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: input.trim(),
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
    };

    const updatedMessages = [...messages, userMsg];
    onMessagesChange(updatedMessages);
    setInput('');
    prefixRef.current = '';
    setLoading(true);

    const assistantMsg: ChatMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
    };

    const history = updatedMessages
      .filter(m => m.content)
      .slice(-10)
      .map(m => ({ role: m.role, content: m.content }));

    try {
      abortRef.current = new AbortController();
      const res = await fetch(`${NLP_API}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content, history }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: 'Request failed' }));
        assistantMsg.content = err.error || `Server error (${res.status})`;
        onMessagesChange([...updatedMessages, assistantMsg]);
        setLoading(false);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        assistantMsg.content = 'Failed to read response stream.';
        onMessagesChange([...updatedMessages, assistantMsg]);
        setLoading(false);
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let currentContent = '';

      onMessagesChange([...updatedMessages, assistantMsg]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data:')) continue;
          const jsonStr = line.slice(5).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);
            if (data.token === '[END]') break;
            if (data.error) {
              currentContent += `\n\nError: ${data.error}`;
              break;
            }
            if (data.token) {
              currentContent += data.token;
              assistantMsg.content = currentContent;
              onMessagesChange([...updatedMessages, { ...assistantMsg }]);
            }
          } catch {
            continue;
          }
        }
      }

      if (!currentContent.trim()) {
        assistantMsg.content = 'No response received. The NLP backend may still be loading the model. Please try again in a moment.';
        onMessagesChange([...updatedMessages, assistantMsg]);
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      assistantMsg.content = 'Cannot connect to NLP backend. Make sure it is running on port 5001.\n\nRun: cd MedAI/MedAI/backend && python run.py';
      onMessagesChange([...updatedMessages, assistantMsg]);
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  };

  return (
    <div className="chat">
      <div className="chat__bg" />
      <div className="chat__decor">
        <div className="chat__decor-circle chat__decor-circle--1" />
        <div className="chat__decor-circle chat__decor-circle--2" />
        <div className="chat__decor-line chat__decor-line--1" />
        <div className="chat__decor-line chat__decor-line--2" />
      </div>

      {!hasUserMessages && (
        <div className="chat__welcome">
          <span className="material-symbols-outlined chat__welcome-icon">forum</span>
          {patient?.name ? (
            <>
              <p className="chat__welcome-text">Welcome, {patient.name}!</p>
              <p className="chat__welcome-sub">How may I help you today?</p>
            </>
          ) : (
            <p className="chat__welcome-text">Welcome! How may I help you today?</p>
          )}
        </div>
      )}

      <div className="chat__messages custom-scrollbar">
        <div className="chat__messages-inner">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat__msg chat__msg--${msg.role}`}>
              <div className="chat__msg-body">
                {msg.content.split('\n').map((p, i) => (
                  <p key={i}>{p}</p>
                ))}
                <CopyButton text={msg.content} />
              </div>
            </div>
          ))}
          {loading && messages[messages.length - 1]?.role === 'user' && (
            <div className="chat__msg chat__msg--assistant">
              <div className="chat__msg-body">
                <p className="chat__typing">Thinking...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat__input-area">
        <div className={`chat__input-wrapper ${voice.state === 'listening' ? 'chat__input-wrapper--recording' : ''}`}>
          {voice.state === 'listening' && (
            <div className="chat__voice-indicator">
              <span className="chat__voice-dot" />
              <Waveform analyserNode={voice.analyserNode} active={voice.state === 'listening'} />
            </div>
          )}
          <input
            type="text"
            className="chat__input"
            placeholder={voice.state === 'listening' ? 'Listening...' : loading ? 'Waiting for response...' : 'Describe symptoms, ask about medications, or request analysis...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={voice.state === 'processing' || loading}
          />
          <div className="chat__input-actions">
            <button
              className={`chat__input-btn ${voice.state === 'listening' ? 'chat__input-btn--recording' : ''}`}
              onClick={voice.toggle}
              title={voice.state === 'listening' ? 'Stop recording' : 'Voice input'}
            >
              <span className="material-symbols-outlined">
                {voice.state === 'listening' ? 'stop' : voice.state === 'processing' ? 'hourglass_empty' : 'mic'}
              </span>
            </button>
            <button className="chat__send-btn" onClick={handleSend} title="Send" disabled={loading}>
              <span className="material-symbols-outlined">{loading ? 'stop' : 'arrow_upward'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
