'use client';

import { useEffect, useRef, useState } from 'react';
import type { Session } from '@/hooks/useSessions';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  onSignOut: () => void;
  sessions: Session[];
  activeId: string | null;
  onSwitch: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
}

export default function Sidebar({ open, onClose, onSignOut, sessions, activeId, onSwitch, onCreate, onDelete, onRename }: SidebarProps) {
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; sessionId: string } | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const isDragging = useRef(false);
  const renameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { onClose(); setContextMenu(null); }
    };
    const handleClick = () => setContextMenu(null);
    if (open) {
      document.addEventListener('keydown', handleEsc);
      document.addEventListener('click', handleClick);
      return () => { document.removeEventListener('keydown', handleEsc); document.removeEventListener('click', handleClick); };
    }
  }, [open, onClose]);

  useEffect(() => {
    if (renamingId && renameInputRef.current) {
      renameInputRef.current.focus();
      renameInputRef.current.select();
    }
  }, [renamingId]);

  const handleContextMenu = (e: React.MouseEvent, sessionId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ x: e.clientX, y: e.clientY, sessionId });
  };

  const handleRenameStart = (sessionId: string, currentTitle: string) => {
    setRenamingId(sessionId);
    setRenameValue(currentTitle);
    setContextMenu(null);
  };

  const handleRenameSubmit = () => {
    if (renamingId && renameValue.trim()) {
      onRename(renamingId, renameValue.trim());
    }
    setRenamingId(null);
  };

  const handleDragStart = (e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    const startX = e.clientX;
    const startWidth = sidebarWidth;

    const onMove = (ev: MouseEvent) => {
      if (!isDragging.current) return;
      const newWidth = Math.max(200, Math.min(500, startWidth + (ev.clientX - startX)));
      setSidebarWidth(newWidth);
    };

    const onUp = () => {
      isDragging.current = false;
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  };

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <>
      <div className={`sidebar-overlay ${open ? 'sidebar-overlay--visible' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${open ? 'sidebar--open' : ''}`} style={{ width: sidebarWidth }}>
        <div className="sidebar__header">
          <span className="sidebar__header-label">SESSIONS</span>
          <button className="sidebar__close-btn" onClick={onClose} title="Close sidebar">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <button className="sidebar__new-session" onClick={onCreate}>
          <span className="material-symbols-outlined sidebar__new-session-icon">add</span>
          NEW SESSION
        </button>

        <nav className="sidebar__nav">
          {sessions.length === 0 ? (
            <div className="sidebar__empty">
              <span className="material-symbols-outlined sidebar__empty-icon">chat_bubble_outline</span>
              <span>No sessions yet</span>
            </div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                className={`sidebar__item ${s.id === activeId ? 'sidebar__item--active' : ''}`}
                onContextMenu={(e) => handleContextMenu(e, s.id)}
              >
                {renamingId === s.id ? (
                  <div className="sidebar__rename">
                    <input
                      ref={renameInputRef}
                      className="sidebar__rename-input"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onBlur={handleRenameSubmit}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleRenameSubmit(); if (e.key === 'Escape') setRenamingId(null); }}
                    />
                  </div>
                ) : (
                  <button className="sidebar__link" onClick={() => onSwitch(s.id)}>
                    <span className="material-symbols-outlined sidebar__link-icon">chat_bubble</span>
                    <div className="sidebar__link-text">
                      <span className="sidebar__link-title">{s.title}</span>
                      <span className="sidebar__link-time">
                        {s.chatMessages.length + s.imagingMessages.length > 0
                          ? `${s.chatMessages.length + s.imagingMessages.length} messages`
                          : formatTime(s.createdAt)}
                      </span>
                    </div>
                  </button>
                )}
                <button className="sidebar__delete-btn" onClick={() => onDelete(s.id)} title="Delete session">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>
            ))
          )}
        </nav>

        <div className="sidebar__footer">
          <button className="sidebar__footer-link" onClick={onSignOut}>
            <span className="material-symbols-outlined sidebar__link-icon">logout</span>
            <span>Logout</span>
          </button>
        </div>

        <div className="sidebar__resize-handle" onMouseDown={handleDragStart} />
      </aside>

      {contextMenu && (
        <div className="context-menu" style={{ top: contextMenu.y, left: contextMenu.x }}>
          <button className="context-menu__item" onClick={() => {
            const s = sessions.find(s => s.id === contextMenu.sessionId);
            if (s) handleRenameStart(s.id, s.title);
          }}>
            <span className="material-symbols-outlined">edit</span>
            Rename
          </button>
          <button className="context-menu__item context-menu__item--danger" onClick={() => { onDelete(contextMenu.sessionId); setContextMenu(null); }}>
            <span className="material-symbols-outlined">delete</span>
            Delete
          </button>
        </div>
      )}
    </>
  );
}
