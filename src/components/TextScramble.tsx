'use client';

import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';

interface TextScrambleProps {
  text: string;
  className?: string;
  delay?: number;
  trigger?: boolean;
}

const chars = '!<>-_\\/[]{}—=+*^?#________';

export default function TextScramble({ text, className = '', delay = 0, trigger = true }: TextScrambleProps) {
  const elRef = useRef<HTMLSpanElement>(null);
  const [hasRun, setHasRun] = useState(false);

  useEffect(() => {
    if (!trigger || hasRun || !elRef.current) return;
    setHasRun(true);

    const el = elRef.current;
    const length = text.length;
    const queue: Array<{ from: string; to: string; start: number; end: number; char?: string }> = [];

    for (let i = 0; i < length; i++) {
      const from = chars[Math.floor(Math.random() * chars.length)];
      const start = Math.floor(Math.random() * 20);
      const end = start + Math.floor(Math.random() * 20);
      queue.push({ from, to: text[i], start, end });
    }

    let frame = 0;
    const totalFrames = 40;

    const update = () => {
      let output = '';
      let complete = 0;

      for (let i = 0; i < queue.length; i++) {
        const item = queue[i];
        if (frame >= item.end) {
          complete++;
          output += item.to;
        } else if (frame >= item.start) {
          if (!item.char || Math.random() < 0.28) {
            item.char = chars[Math.floor(Math.random() * chars.length)];
          }
          output += `<span class="scramble-char">${item.char}</span>`;
        } else {
          output += item.from;
        }
      }

      el.innerHTML = output;
      frame++;

      if (frame < totalFrames) {
        gsap.delayedCall(0.03, update);
      }
    };

    gsap.delayedCall(delay, () => {
      frame = 0;
      update();
    });
  }, [text, delay, trigger, hasRun]);

  return <span ref={elRef} className={className} />;
}
