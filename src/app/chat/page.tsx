'use client';

import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Sidebar from '@/components/dashboard/Sidebar';
import ChatTab from '@/components/dashboard/ChatTab';
import ImageAnalysisTab from '@/components/dashboard/ImageAnalysisTab';
import { useSessions, ChatMessage, ImageItem } from '@/hooks/useSessions';

type Tab = 'chat' | 'imaging';

export default function ChatPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const {
    sessions,
    activeSession,
    activeId,
    switchSession,
    createSession,
    deleteSession,
    updateSession,
  } = useSessions();

  useEffect(() => {
    if (status === 'unauthenticated') router.push('/login');
  }, [status, router]);

  useEffect(() => {
    document.body.classList.remove('loading');
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem('nidaan_dark_mode');
    if (saved === 'true') setDarkMode(true);
  }, []);

  useEffect(() => {
    localStorage.setItem('nidaan_dark_mode', String(darkMode));
  }, [darkMode]);

  if (status === 'loading') {
    return <div className="dash-loading"><div className="dash-loading__spinner" /></div>;
  }

  if (!session || !activeSession) return null;

  const userName = session.user?.name || 'User';
  const userEmail = session.user?.email || '';
  const userImage = session.user?.image;

  return (
    <div className={`dash ${darkMode ? 'dash--dark' : ''}`}>
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onSignOut={() => signOut({ callbackUrl: '/login' })}
        sessions={sessions}
        activeId={activeId}
        onSwitch={(id) => { switchSession(id); setSidebarOpen(false); }}
        onCreate={() => { createSession(); setSidebarOpen(false); }}
        onDelete={deleteSession}
        onRename={(id, title) => updateSession(id, { title })}
      />

      <div className="dash__main">
        <header className="dash__header">
          <div className="dash__header-left">
            <button className="dash__menu-btn" onClick={() => setSidebarOpen(true)} title="Open sidebar">
              <span className="material-symbols-outlined">menu</span>
            </button>
          </div>

          <div className="dash__switcher">
            <button
              className={`dash__switcher-btn ${activeTab === 'chat' ? 'dash__switcher-btn--active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              Consult
            </button>
            <button
              className={`dash__switcher-btn ${activeTab === 'imaging' ? 'dash__switcher-btn--active' : ''}`}
              onClick={() => setActiveTab('imaging')}
            >
              Imaging
            </button>
            <span
              className="dash__switcher-indicator"
              style={{ transform: activeTab === 'imaging' ? 'translateX(100%)' : 'translateX(0)' }}
            />
          </div>

          <div className="dash__header-right">
            <div className="dash__dropdown-wrap">
              <button className="dash__icon-btn" title="Settings" onClick={() => { setSettingsOpen(!settingsOpen); setProfileOpen(false); }}>
                <span className="material-symbols-outlined">settings</span>
              </button>
              {settingsOpen && (
                <div className="dash__dropdown">
                  <div className="dash__dropdown-title">Settings</div>
                  <label className="dash__dropdown-row">
                    <span>Dark mode</span>
                    <button className={`dash__toggle ${darkMode ? 'dash__toggle--on' : ''}`} onClick={() => setDarkMode(!darkMode)}>
                      <span className="dash__toggle-knob" />
                    </button>
                  </label>
                  <label className="dash__dropdown-row">
                    <span>Language</span>
                    <select className="dash__dropdown-select">
                      <option>English</option>
                      <option>Nepali</option>
                      <option>Hindi</option>
                    </select>
                  </label>
                  <label className="dash__dropdown-row">
                    <span>Voice input</span>
                    <input type="checkbox" defaultChecked className="dash__dropdown-check" />
                  </label>
                  <label className="dash__dropdown-row">
                    <span>Notifications</span>
                    <input type="checkbox" defaultChecked className="dash__dropdown-check" />
                  </label>
                </div>
              )}
            </div>
            <div className="dash__dropdown-wrap">
              <button className="dash__icon-btn" title="Account" onClick={() => { setProfileOpen(!profileOpen); setSettingsOpen(false); }}>
                <span className="material-symbols-outlined">account_circle</span>
              </button>
              {profileOpen && (
                <div className="dash__dropdown dash__dropdown--right">
                  <div className="dash__dropdown-profile">
                    {userImage ? (
                      <img src={userImage} alt="" className="dash__dropdown-avatar" />
                    ) : (
                      <div className="dash__dropdown-avatar-placeholder">
                        <span className="material-symbols-outlined">person</span>
                      </div>
                    )}
                    <div>
                      <div className="dash__dropdown-name">{userName}</div>
                      <div className="dash__dropdown-email">{userEmail}</div>
                    </div>
                  </div>
                  <div className="dash__dropdown-divider" />
                  <button className="dash__dropdown-action" onClick={() => signOut({ callbackUrl: '/login' })}>
                    <span className="material-symbols-outlined">logout</span>
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className="dash__content">
          {activeTab === 'chat' ? (
            <ChatTab
              messages={activeSession.chatMessages}
              onMessagesChange={(msgs: ChatMessage[]) => updateSession(activeId!, { chatMessages: msgs })}
            />
          ) : (
            <ImageAnalysisTab
              images={activeSession.images}
              onImagesChange={(imgs: ImageItem[]) => updateSession(activeId!, { images: imgs })}
              chatMessages={activeSession.imagingMessages}
              onChatMessagesChange={(msgs: ChatMessage[]) => updateSession(activeId!, { imagingMessages: msgs })}
            />
          )}
        </div>
      </div>

      {(settingsOpen || profileOpen) && (
        <div className="dash__dropdown-backdrop" onClick={() => { setSettingsOpen(false); setProfileOpen(false); }} />
      )}
    </div>
  );
}
