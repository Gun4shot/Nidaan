'use client';

import { useState, useRef, useEffect } from 'react';
import type { ChatMessage, ImageItem } from '@/hooks/useSessions';
import { useVoiceInput } from '@/hooks/useVoiceInput';
import Waveform from './Waveform';

type LayoutMode = 'single' | 'grid' | 'compare';

interface ImageAnalysisTabProps {
  images: ImageItem[];
  onImagesChange: (imgs: ImageItem[]) => void;
  chatMessages: ChatMessage[];
  onChatMessagesChange: (msgs: ChatMessage[]) => void;
}

export default function ImageAnalysisTab({ images, onImagesChange, chatMessages, onChatMessagesChange }: ImageAnalysisTabProps) {
  const [activeImage, setActiveImage] = useState<number>(0);
  const [input, setInput] = useState('');
  const [zoom, setZoom] = useState(1);
  const [layout, setLayout] = useState<LayoutMode>('single');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const prefixRef = useRef('');
  const wasListeningRef = useRef(false);

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

  const currentImage = images[activeImage];

  useEffect(() => {
    if (chatMessages.length === 0) {
      onChatMessagesChange([{
        id: 1,
        role: 'assistant',
        content: 'Upload medical images and I\'ll help you analyze them. Ask about findings, differentials, or measurements.',
        time: '',
      }]);
    }
  }, []);

  useEffect(() => {
    if (activeImage >= images.length) {
      setActiveImage(Math.max(0, images.length - 1));
    }
  }, [images.length, activeImage]);

  const handleUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newImages: ImageItem[] = [];
    for (const file of Array.from(files)) {
      const url = URL.createObjectURL(file);
      newImages.push({
        id: Date.now() + Math.random(),
        name: file.name,
        src: url,
      });
    }
    onImagesChange([...images, ...newImages]);
  };

  const handleRemoveImage = (index: number) => {
    const newImages = images.filter((_, i) => i !== index);
    onImagesChange(newImages);
  };

  const handleSend = () => {
    if (!input.trim()) return;
    onChatMessagesChange([
      ...chatMessages,
      { id: Date.now(), role: 'user', content: input.trim(), time: '' },
    ]);
    setInput('');
  };

  return (
    <div className="imaging">
      <div className="chat__bg" />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        className="imaging__file-input"
        onChange={handleFileChange}
      />

      <div className="imaging__viewer">
        {images.length === 0 ? (
          <div className="imaging__upload-zone" onClick={handleUpload}>
            <span className="material-symbols-outlined imaging__upload-icon">cloud_upload</span>
            <p className="imaging__upload-title">Upload medical images</p>
            <p className="imaging__upload-desc">Drop files here or click to browse. Supports DICOM, JPEG, PNG.</p>
          </div>
        ) : (
          <>
            <div className="imaging__viewer-toolbar">
              <div className="imaging__viewer-info">
                <span className="imaging__viewer-name">{currentImage?.name}</span>
                <span className="imaging__viewer-count">{activeImage + 1} / {images.length}</span>
              </div>
              <div className="imaging__viewer-tools">
                <div className="imaging__layout-btns">
                  <button className={`imaging__layout-btn ${layout === 'single' ? 'imaging__layout-btn--active' : ''}`} onClick={() => setLayout('single')} title="Single view">
                    <span className="material-symbols-outlined">crop_square</span>
                  </button>
                  <button className={`imaging__layout-btn ${layout === 'grid' ? 'imaging__layout-btn--active' : ''}`} onClick={() => setLayout('grid')} title="Grid view">
                    <span className="material-symbols-outlined">grid_view</span>
                  </button>
                  <button className={`imaging__layout-btn ${layout === 'compare' ? 'imaging__layout-btn--active' : ''}`} onClick={() => setLayout('compare')} title="Compare view">
                    <span className="material-symbols-outlined">view_column</span>
                  </button>
                </div>
                <span className="imaging__toolbar-divider" />
                <button className="imaging__tool-btn" onClick={() => setZoom((z) => Math.min(z + 0.25, 3))}>
                  <span className="material-symbols-outlined">zoom_in</span>
                </button>
                <button className="imaging__tool-btn" onClick={() => setZoom((z) => Math.max(z - 0.25, 0.5))}>
                  <span className="material-symbols-outlined">zoom_out</span>
                </button>
                <button className="imaging__tool-btn" onClick={() => setZoom(1)}>
                  <span className="material-symbols-outlined">fit_screen</span>
                </button>
                <span className="imaging__toolbar-divider" />
                <button className="imaging__tool-btn" onClick={() => { handleRemoveImage(activeImage); }} title="Remove current image">
                  <span className="material-symbols-outlined">delete</span>
                </button>
                <button className="imaging__tool-btn" onClick={handleUpload}>
                  <span className="material-symbols-outlined">add_photo_alternate</span>
                </button>
              </div>
            </div>

            <div className={`imaging__canvas imaging__canvas--${layout}`}>
              {layout === 'single' && currentImage && (
                <img src={currentImage.src} alt={currentImage.name} className="imaging__canvas-img" style={{ transform: `scale(${zoom})` }} />
              )}
              {layout === 'grid' && images.map((img) => (
                <div key={img.id} className="imaging__grid-cell">
                  <img src={img.src} alt={img.name} className="imaging__canvas-img" />
                </div>
              ))}
              {layout === 'compare' && images.length >= 2 && (
                <>
                  <div className="imaging__compare-pane">
                    <img src={images[0].src} alt={images[0].name} className="imaging__canvas-img" />
                  </div>
                  <div className="imaging__compare-pane">
                    <img src={images[Math.min(1, images.length - 1)].src} alt="Compare" className="imaging__canvas-img" />
                  </div>
                </>
              )}
            </div>

            <div className="imaging__thumbs">
              {images.map((img, i) => (
                <div key={img.id} className={`imaging__thumb-wrap ${i === activeImage ? 'imaging__thumb-wrap--active' : ''}`}>
                  <button
                    className="imaging__thumb"
                    onClick={() => { setActiveImage(i); setZoom(1); }}
                  >
                    <img src={img.src} alt={img.name} />
                  </button>
                  <button className="imaging__thumb-remove" onClick={(e) => { e.stopPropagation(); handleRemoveImage(i); }} title="Remove image">
                    <span className="material-symbols-outlined">close</span>
                  </button>
                </div>
              ))}
              <button className="imaging__thumb imaging__thumb--add" onClick={handleUpload}>
                <span className="material-symbols-outlined">add_photo_alternate</span>
              </button>
            </div>
          </>
        )}
      </div>

      <div className="imaging__chat">
        <div className="imaging__chat-messages custom-scrollbar">
          {chatMessages.map((msg) => (
            <div key={msg.id} className={`imaging__chat-msg imaging__chat-msg--${msg.role}`}>
              <div className="imaging__chat-msg-body">{msg.content}</div>
            </div>
          ))}
        </div>

        <div className="imaging__chat-input-area">
          <div className={`imaging__chat-input-wrapper ${voice.state === 'listening' ? 'imaging__chat-input-wrapper--recording' : ''}`}>
            {voice.state === 'listening' && (
              <div className="imaging__voice-indicator">
                <span className="imaging__voice-dot" />
                <Waveform analyserNode={voice.analyserNode} active={voice.state === 'listening'} />
              </div>
            )}
            <textarea
              className="imaging__chat-input custom-scrollbar"
              placeholder={voice.state === 'listening' ? 'Listening...' : 'Ask about findings...'}
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={voice.state === 'processing'}
            />
            <div className="imaging__chat-input-actions">
              <button
                className={`imaging__voice-btn ${voice.state === 'listening' ? 'imaging__voice-btn--recording' : ''}`}
                onClick={voice.toggle}
                title={voice.state === 'listening' ? 'Stop recording' : 'Voice input'}
              >
                <span className="material-symbols-outlined">
                  {voice.state === 'listening' ? 'stop' : voice.state === 'processing' ? 'hourglass_empty' : 'mic'}
                </span>
              </button>
              <button className="imaging__chat-send" onClick={handleSend}>
                <span className="material-symbols-outlined">arrow_upward</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
