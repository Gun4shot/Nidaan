'use client';

import { useState, useEffect, useCallback } from 'react';

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  time: string;
}

export interface ImageItem {
  id: number;
  name: string;
  src: string;
}

export interface PatientInfo {
  name: string;
  age: string;
  gender: string;
}

export interface Session {
  id: string;
  title: string;
  createdAt: string;
  patient: PatientInfo | null;
  chatMessages: ChatMessage[];
  images: ImageItem[];
  imagingMessages: ChatMessage[];
}

const STORAGE_KEY = 'nidaan_sessions';
const ACTIVE_KEY = 'nidaan_active_session';

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

function loadSessions(): Session[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveSessions(sessions: Session[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

function loadActiveId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACTIVE_KEY);
}

function saveActiveId(id: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACTIVE_KEY, id);
}

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    const loaded = loadSessions();
    const savedActive = loadActiveId();

    if (loaded.length === 0) {
      const first: Session = {
        id: generateId(),
        title: 'New session',
        createdAt: new Date().toISOString(),
        patient: null,
        chatMessages: [],
        images: [],
        imagingMessages: [],
      };
      setSessions([first]);
      setActiveId(first.id);
      saveSessions([first]);
      saveActiveId(first.id);
    } else {
      setSessions(loaded);
      setActiveId(savedActive && loaded.find(s => s.id === savedActive) ? savedActive : loaded[0].id);
    }
  }, []);

  const activeSession = sessions.find(s => s.id === activeId) || null;

  const switchSession = useCallback((id: string) => {
    setActiveId(id);
    saveActiveId(id);
  }, []);

  const createSession = useCallback(() => {
    const newSession: Session = {
      id: generateId(),
      title: 'New session',
      createdAt: new Date().toISOString(),
      patient: null,
      chatMessages: [],
      images: [],
      imagingMessages: [],
    };
    setSessions(prev => {
      const next = [newSession, ...prev];
      saveSessions(next);
      return next;
    });
    setActiveId(newSession.id);
    saveActiveId(newSession.id);
    return newSession.id;
  }, []);

  const deleteSession = useCallback((id: string) => {
    setSessions(prev => {
      const next = prev.filter(s => s.id !== id);
      saveSessions(next);
      if (next.length === 0) {
        const fresh: Session = {
          id: generateId(),
          title: 'New session',
          createdAt: new Date().toISOString(),
          patient: null,
          chatMessages: [],
          images: [],
          imagingMessages: [],
        };
        const all = [fresh];
        saveSessions(all);
        setActiveId(fresh.id);
        saveActiveId(fresh.id);
        return all;
      }
      if (activeId === id) {
        setActiveId(next[0].id);
        saveActiveId(next[0].id);
      }
      return next;
    });
  }, [activeId]);

  const updateSession = useCallback((id: string, updates: Partial<Session>) => {
    setSessions(prev => {
      const next = prev.map(s => s.id === id ? { ...s, ...updates } : s);
      saveSessions(next);
      return next;
    });
  }, []);

  return {
    sessions,
    activeSession,
    activeId,
    switchSession,
    createSession,
    deleteSession,
    updateSession,
  };
}
