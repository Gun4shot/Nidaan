'use client';

import { useEffect, useRef } from 'react';
import gsap from 'gsap';

export default function FooterSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const ctaRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const section = sectionRef.current;
    const cta = ctaRef.current;
    if (!section || !cta) return;

    gsap.set(cta, { opacity: 0, scale: 0.6 });

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          gsap.to(cta, {
            opacity: 1,
            scale: 1,
            duration: 1.2,
            ease: 'power4.out',
          });
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );

    observer.observe(section);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="footer-section" id="contact">
      <a ref={ctaRef} href="/chat" className="footer-section__cta">
        <span className="footer-section__cta-text">
          HEALTHCARE<br />FOR EVERYONE
        </span>
      </a>

      <footer className="footer-section__bar">
        <span className="footer-section__copy">© 2026 NIDAAN. OPEN SOURCE MEDICAL AI.</span>
        <div className="footer-section__links">
          <a href="https://github.com/ruslanmv/ai-medical-chatbot">GITHUB</a>
          <a href="#about">ABOUT</a>
          <a href="/chat">TRY IT</a>
        </div>
      </footer>
    </section>
  );
}
