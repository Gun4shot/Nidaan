'use client';

import { useState, useRef, useEffect } from 'react';
import type { ChatMessage } from '@/hooks/useSessions';
import { useVoiceInput } from '@/hooks/useVoiceInput';
import Waveform from './Waveform';

interface ChatTabProps {
  messages: ChatMessage[];
  onMessagesChange: (msgs: ChatMessage[]) => void;
}

export default function ChatTab({ messages, onMessagesChange }: ChatTabProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prefixRef = useRef('');
  const wasListeningRef = useRef(false);

  const voice = useVoiceInput({
    onInterim: (text) => {
      setInput(prefixRef.current + text);
    },
    onResult: (text) => {
      setInput(prefixRef.current + text);
      prefixRef.current = '';
    },
    onError: (err) => {
      console.error('Voice error:', err);
    },
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

  useEffect(() => {
    if (messages.length === 0) {
      onMessagesChange([{
        id: 1,
        role: 'assistant',
        content: 'Hello! How may I help you today?',
        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
      }]);
    }
  }, []);

  const handleSend = () => {
    if (!input.trim()) return;

    const newMsg: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: input.trim(),
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
    };

    onMessagesChange([...messages, newMsg]);
    setInput('');
    prefixRef.current = '';
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

      <div className="chat__messages custom-scrollbar">
        <div className="chat__messages-inner">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat__msg chat__msg--${msg.role}`}>
              <div className="chat__msg-body">
                {msg.content.split('\n').map((p, i) => (
                  <p key={i}>{p}</p>
                ))}
              </div>
            </div>
          ))}
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
            placeholder={voice.state === 'listening' ? 'Listening...' : 'Describe symptoms, ask about medications, or request analysis...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={voice.state === 'processing'}
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
            <button className="chat__send-btn" onClick={handleSend} title="Send">
              <span className="material-symbols-outlined">arrow_upward</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
