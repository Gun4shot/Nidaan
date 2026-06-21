'use client';

import { useEffect, useRef, useState } from 'react';
import TextScramble from './TextScramble';

const capabilities = [
  { num: '01', title: 'DIAGNOSTIC CHAT' },
  { num: '02', title: 'MEDICAL IMAGING' },
  { num: '03', title: 'VOICE INPUT' },
  { num: '04', title: 'HEALTH TRACKER' },
];

export default function CapabilitiesSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(section);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="capabilities" id="capabilities">
      <div className="capabilities__hero">
        <h1 className="capabilities__hero-title">
          <TextScramble text="CAPABILITIES" delay={0} trigger={isVisible} />
        </h1>
        <div className="capabilities__hero-label">
          <span className="capabilities__hero-line" />
          <span>Systematic Medical Architecture</span>
        </div>
      </div>

      <div className="capabilities__grid">
        {capabilities.map((cap) => (
          <div key={cap.num} className="capabilities__card">
            <div className="capabilities__card-num">{cap.num}</div>
            <h3 className="capabilities__card-title">{cap.title}</h3>
            <div className="capabilities__card-link">
              <span>EXPLORE</span>
              <span className="capabilities__card-arrow">→</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
