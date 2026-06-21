'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

type VoiceState = 'idle' | 'listening' | 'processing' | 'error';

interface UseVoiceInputOptions {
  onResult: (text: string) => void;
  onInterim?: (text: string) => void;
  onError?: (error: string) => void;
  lang?: string;
}

interface UseVoiceInputReturn {
  state: VoiceState;
  isSupported: boolean;
  toggle: () => void;
  stop: () => void;
  analyserNode: AnalyserNode | null;
}

export function useVoiceInput({ onResult, onInterim, onError, lang = 'en-US' }: UseVoiceInputOptions): UseVoiceInputReturn {
  const [state, setState] = useState<VoiceState>('idle');
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const engineRef = useRef<'webspeech' | 'whisper' | null>(null);
  const finalTranscriptRef = useRef('');
  const onResultRef = useRef(onResult);
  const onInterimRef = useRef(onInterim);
  const onErrorRef = useRef(onError);

  useEffect(() => { onResultRef.current = onResult; }, [onResult]);
  useEffect(() => { onInterimRef.current = onInterim; }, [onInterim]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);

  const SpeechRecognition = typeof window !== 'undefined'
    ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    : null;

  const isWebSpeechSupported = !!SpeechRecognition;

  const setupAnalyser = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      setAnalyserNode(analyser);
    } catch {}
  }, []);

  const cleanup = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch {}
      recognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch {}
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setAnalyserNode(null);
    engineRef.current = null;
    finalTranscriptRef.current = '';
  }, []);

  const startWhisperRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      setAnalyserNode(analyser);

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        setState('processing');
        const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType });

        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');

          const response = await fetch('/api/voice/transcribe', {
            method: 'POST',
            body: formData,
          });

          const data = await response.json();

          if (data.transcript) {
            onResultRef.current(data.transcript);
            setState('idle');
          } else {
            setState('error');
            onErrorRef.current?.(data.error || 'Transcription failed');
            setTimeout(() => setState('idle'), 2000);
          }
        } catch (err) {
          setState('error');
          onErrorRef.current?.('Network error');
          setTimeout(() => setState('idle'), 2000);
        }

        cleanup();
      };

      mediaRecorder.start(100);
      setState('listening');
      engineRef.current = 'whisper';
    } catch (err) {
      setState('error');
      onErrorRef.current?.('Microphone access denied');
      setTimeout(() => setState('idle'), 2000);
      cleanup();
    }
  }, [cleanup]);

  const startWebSpeech = useCallback(() => {
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang;
    recognition.maxAlternatives = 1;
    recognitionRef.current = recognition;
    engineRef.current = 'webspeech';
    finalTranscriptRef.current = '';

    recognition.onstart = () => {
      setState('listening');
      setupAnalyser();
    };

    recognition.onresult = (event: any) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        if (result.isFinal) {
          finalTranscriptRef.current += transcript + ' ';
        } else {
          interim += transcript;
        }
      }
      const fullText = finalTranscriptRef.current + interim;
      onInterimRef.current?.(fullText);
    };

    recognition.onspeechend = () => {
      recognition.stop();
    };

    recognition.onend = () => {
      const text = finalTranscriptRef.current.trim();
      if (text) {
        onResultRef.current(text);
      }
      setState('idle');
      cleanup();
    };

    recognition.onerror = (event: any) => {
      if (event.error === 'not-allowed') {
        setState('error');
        onErrorRef.current?.('Microphone access denied');
        setTimeout(() => setState('idle'), 2000);
      } else if (event.error === 'no-speech') {
        setState('idle');
      } else if (event.error === 'aborted') {
        setState('idle');
      } else {
        startWhisperRecording();
        return;
      }
      cleanup();
    };

    recognition.start();
  }, [lang, cleanup, setupAnalyser, startWhisperRecording, SpeechRecognition]);

  const toggle = useCallback(() => {
    if (state === 'listening' || state === 'processing') {
      if (engineRef.current === 'webspeech' && recognitionRef.current) {
        recognitionRef.current.stop();
      } else if (engineRef.current === 'whisper' && mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      return;
    }

    if (isWebSpeechSupported) {
      startWebSpeech();
    } else {
      startWhisperRecording();
    }
  }, [state, isWebSpeechSupported, startWebSpeech, startWhisperRecording]);

  const stop = useCallback(() => {
    if (state !== 'idle') {
      if (engineRef.current === 'webspeech' && recognitionRef.current) {
        recognitionRef.current.stop();
      } else if (engineRef.current === 'whisper' && mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
    }
  }, [state]);

  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return {
    state,
    isSupported: isWebSpeechSupported || typeof navigator !== 'undefined' && !!navigator.mediaDevices,
    toggle,
    stop,
    analyserNode,
  };
}
