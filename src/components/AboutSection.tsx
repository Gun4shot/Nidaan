'use client';

import { useEffect, useRef, useState } from 'react';
import TextScramble from './TextScramble';

export default function AboutSection() {
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
      { threshold: 0.2 }
    );

    observer.observe(section);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="about-section" id="about">
      <div className="about-section__left">
        <div className="about-section__label">
          <span className="about-section__label-line" />
          <span>What is Nidaan</span>
        </div>

        <h2 className="about-section__title">
          <TextScramble
            text="Free AI medical"
            className="about-section__title-line"
            delay={0}
            trigger={isVisible}
          />
          <TextScramble
            text="guidance for everyone,"
            className="about-section__title-line"
            delay={0.1}
            trigger={isVisible}
          />
          <TextScramble
            text="in every language."
            className="about-section__title-line"
            delay={0.2}
            trigger={isVisible}
          />
        </h2>
      </div>

      <div className="about-section__right">
        <div className="about-section__body">
          <p className="about-section__paragraph about-section__paragraph--lg">
            <TextScramble
              text="Fine-tuned on 250,000+ clinical Q&A pairs. Grounded in WHO, CDC, and NHS guidelines."
              delay={0.5}
              trigger={isVisible}
            />
          </p>
          <p className="about-section__paragraph">
            <TextScramble
              text="Understands symptoms, analyzes medical images, and speaks 13 languages — including Nepali."
              delay={0.75}
              trigger={isVisible}
            />
          </p>
          <p className="about-section__paragraph">
            <TextScramble
              text="Open source. No sign-up. No tracking. Free forever."
              delay={1.0}
              trigger={isVisible}
            />
          </p>
        </div>
      </div>
    </section>
  );
}
