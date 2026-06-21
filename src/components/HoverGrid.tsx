'use client';

import { useEffect, useRef, useCallback } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import AboutSection from './AboutSection';
import FooterSection from './FooterSection';

gsap.registerPlugin(ScrollTrigger);

interface WorkItem {
  id: string;
  title: string;
  bgId: string;
  images: Array<{
    pos: string;
    dir: string;
    src: string;
  }>;
}

const workItems: WorkItem[] = [
  {
    id: 'content-1',
    title: 'Live chat',
    bgId: 'bg-1',
    images: [
      { pos: 'pos-1', dir: 'right', src: '/media/p4.png' },
      { pos: 'pos-2', dir: 'left', src: '/media/2.jpg' },
      { pos: 'pos-3', dir: 'top', src: '/media/3.jpg' },
    ],
  },
  {
    id: 'content-2',
    title: 'Medical Image Analysis',
    bgId: 'bg-2',
    images: [
      { pos: 'pos-4', dir: 'bottom', src: '/media/p1.png' },
      { pos: 'pos-5', dir: 'right', src: '/media/p2.jpg' },
      { pos: 'pos-6', dir: 'right', src: '/media/p3.jpg' },
    ],
  },
  {
    id: 'content-3',
    title: 'Speech input',
    bgId: 'bg-3',
    images: [
      { pos: 'pos-7', dir: 'right', src: '/media/7.jpg' },
      { pos: 'pos-8', dir: 'bottom', src: '/media/8.jpg' },
      { pos: 'pos-9', dir: 'left', src: '/media/9.jpg' },
    ],
  },
  {
    id: 'content-4',
    title: 'Translation',
    bgId: 'bg-4',
    images: [
      { pos: 'pos-10', dir: 'left', src: '/media/10.jpg' },
      { pos: 'pos-11', dir: 'right', src: '/media/11.jpg' },
      { pos: 'pos-12', dir: 'right', src: '/media/12.jpg' },
    ],
  },
  {
    id: 'content-5',
    title: 'Hardware analytics',
    bgId: 'bg-5',
    images: [
      { pos: 'pos-13', dir: 'right', src: '/media/13.jpg' },
      { pos: 'pos-14', dir: 'bottom', src: '/media/14.jpg' },
      { pos: 'pos-15', dir: 'right', src: '/media/15.jpg' },
    ],
  },
];

const clipPathDirections: Record<string, string> = {
  right: 'polygon(0% 0%, 0% 0%, 0% 100%, 0% 100%)',
  left: 'polygon(100% 0%, 100% 0%, 100% 100%, 100% 100%)',
  top: 'polygon(0% 100%, 100% 100%, 100% 100%, 0% 100%)',
  bottom: 'polygon(0% 0%, 100% 0%, 100% 0%, 0% 0%)',
};

const getClipPath = (dir: string) => ({
  from: clipPathDirections[dir] || 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)',
  to: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)',
});

export default function HoverGrid() {
  const containerRef = useRef<HTMLDivElement>(null);
  const workNavRef = useRef<HTMLElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const bgImageRef = useRef<HTMLImageElement>(null);
  const frameRef = useRef<HTMLDivElement>(null);
  const timelinesRef = useRef<Map<string, gsap.core.Timeline>>(new Map());

  const toggleWork = useCallback((href: string, isShowing: boolean) => {
    const contentElement = document.querySelector(href) as HTMLElement;
    if (!contentElement) return;

    const bgId = contentElement.dataset.bg;
    const bgElement = document.getElementById(bgId || '');
    const contentTitle = contentElement.querySelector('.content__title') as HTMLElement;
    const contentImages = [...contentElement.querySelectorAll('.content__img')] as HTMLElement[];
    const contentInnerImages = [...contentElement.querySelectorAll('.content__img-inner')] as HTMLElement[];

    const key = href;
    const existingTl = timelinesRef.current.get(key);
    if (existingTl) {
      existingTl.kill();
    }

    if (isShowing) {
      gsap.set(contentElement, { zIndex: 1 });
      contentElement.classList.add('content--current');

      const tl = gsap.timeline({
        defaults: { duration: 0.95, ease: 'power4' },
      })
        .set(bgElement, { opacity: 1 })
        .fromTo(
          contentTitle,
          { opacity: 0, scale: 0.9 },
          { opacity: 1, scale: 1 },
          0
        )
        .fromTo(
          contentImages,
          {
            xPercent: () => gsap.utils.random(-10, 10),
            yPercent: () => gsap.utils.random(-10, 10),
            filter: 'brightness(300%)',
            clipPath: (_index: number, target: HTMLElement) => {
              const dir = target.dataset.dir || 'right';
              return getClipPath(dir).from;
            },
          },
          {
            xPercent: 0,
            yPercent: 0,
            filter: 'brightness(100%)',
            clipPath: (_index: number, target: HTMLElement) => {
              const dir = target.dataset.dir || 'right';
              return getClipPath(dir).to;
            },
          },
          0
        )
        .fromTo(
          contentInnerImages,
          { scale: 1.5 },
          { scale: 1 },
          0
        );

      timelinesRef.current.set(key, tl);
    } else {
      gsap.set(contentElement, { zIndex: 0 });

      const tl = gsap.timeline({
        defaults: { duration: 0.95, ease: 'power4' },
        onComplete: () => {
          contentElement.classList.remove('content--current');
        },
      })
        .set(bgElement, { opacity: 0 }, 0.05)
        .to(contentTitle, { opacity: 0 }, 0)
        .to(
          contentImages,
          {
            clipPath: (_index: number, target: HTMLElement) => {
              const dir = target.dataset.dir || 'right';
              return getClipPath(dir).from;
            },
          },
          0
        )
        .to(contentInnerImages, { scale: 1.5 }, 0);

      timelinesRef.current.set(key, tl);
    }
  }, []);

  useEffect(() => {
    const workNav = workNavRef.current;
    const title = titleRef.current;
    const video = videoRef.current;
    const bgImage = bgImageRef.current;
    const frame = frameRef.current;
    if (!workNav || !title || !video || !bgImage || !frame) return;

    const workLinks = [...workNav.querySelectorAll('a')] as HTMLElement[];
    const hoverTimers = new Map<HTMLElement, ReturnType<typeof setTimeout>>();

    workLinks.forEach((workLink) => {
      workLink.addEventListener('mouseenter', (event) => {
        const target = event.currentTarget as HTMLElement;
        const timer = setTimeout(() => {
          const href = target.getAttribute('href');
          if (href) toggleWork(href, true);
        }, 30);
        hoverTimers.set(target, timer);
      });

      workLink.addEventListener('mouseleave', (event) => {
        const target = event.currentTarget as HTMLElement;
        const timer = hoverTimers.get(target);
        if (timer) {
          clearTimeout(timer);
          hoverTimers.delete(target);
        }
        const href = target.getAttribute('href');
        if (href) toggleWork(href, false);
      });
    });

    const handleNavEnter = () => {
      gsap.killTweensOf([video, title]);
      gsap.to([video, title], {
        duration: 0.6,
        ease: 'power4',
        opacity: 0,
      });
    };

    const handleNavLeave = () => {
      gsap.killTweensOf([video, title]);
      gsap.to([video, title], {
        duration: 0.6,
        ease: 'sine.in',
        opacity: 1,
      });
    };

    workNav.addEventListener('mouseenter', handleNavEnter);
    workNav.addEventListener('mouseleave', handleNavLeave);

    document.body.classList.remove('loading');

    const scrollContainer = document.querySelector('.scroll-snap-container');
    if (!scrollContainer) return;

    const st = ScrollTrigger.create({
      trigger: scrollContainer,
      scroller: scrollContainer,
      start: 'top top',
      end: () => window.innerHeight,
      scrub: 0.5,
      onUpdate: (self) => {
        const progress = self.progress;
        const videoOpacity = 1 - progress;
        const imageOpacity = progress;

        video.style.opacity = String(Math.max(0, videoOpacity));
        bgImage.style.opacity = String(Math.min(1, imageOpacity));
        bgImage.style.filter = `brightness(${0.15 + progress * 0.85})`;

        frame.style.opacity = String(Math.max(0, 1 - progress * 2.5));
        frame.style.pointerEvents = progress > 0.3 ? 'none' : '';
      },
    });

    return () => {
      hoverTimers.forEach((timer) => clearTimeout(timer));
      workNav.removeEventListener('mouseenter', handleNavEnter);
      workNav.removeEventListener('mouseleave', handleNavLeave);
      timelinesRef.current.forEach((tl) => tl.kill());
      st.kill();
    };
  }, [toggleWork]);

  return (
    <>
      <div className="scroll-snap-container">
        <section className="snap-section snap-section--landing">
          <div className="frame" ref={frameRef}>
            <nav className="frame__works" ref={workNavRef}>
              <span>Our services</span>
              {workItems.map((item) => (
                <a key={item.id} href={`#${item.id}`}>
                  {item.title}
                </a>
              ))}
            </nav>

            <div className="frame__tagline">
              Connecting health with AI through fine-tuned language models trained on clinical datasets. Open-source medical intelligence for everyone.
            </div>

            <div className="frame__site">Nidaan</div>
            <div className="frame__year">© 2026</div>
            <div className="frame__contact" />
            <div className="frame__menu" />

            <div className="frame__links">
              <a className="frame__back" href="#about">
                About Us
              </a>
              <a className="frame__github" href="https://github.com/Gun4shot/Nidaan">
                GitHub
              </a>
            </div>

            <h2 className="frame__title-main" ref={titleRef}>
              <span className="title-nidaan">Nidaan</span>
              <a href="/login" className="title-cta">
                Start Here →
              </a>
            </h2>

            <div className="frame__content">
              {workItems.map((item) => (
                <div
                  key={item.id}
                  className="content"
                  id={item.id}
                  data-bg={item.bgId}
                >
                  <h2 className="content__title">{item.title}</h2>
                  {item.images.map((img, idx) => (
                    <div
                      key={idx}
                      className={`content__img ${img.pos}`}
                      data-dir={img.dir}
                    >
                      <div
                        className="content__img-inner"
                        style={{ backgroundImage: `url(${img.src})` }}
                      />
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="snap-section snap-section--about">
          <AboutSection />
        </section>

        <section className="snap-section snap-section--footer">
          <FooterSection />
        </section>
      </div>

      <div className="background">
        <div id="bg-1" className="background__image" style={{ backgroundImage: 'url(/media/beige1.jpg)' }} />
        <div id="bg-2" className="background__image" style={{ backgroundImage: 'url(/media/red1.jpg)' }} />
        <div id="bg-3" className="background__image" style={{ backgroundImage: 'url(/media/pink.jpg)' }} />
        <div id="bg-4" className="background__image" style={{ backgroundImage: 'url(/media/beige2.jpg)' }} />
        <div id="bg-5" className="background__image" style={{ backgroundImage: 'url(/media/red2.jpg)' }} />
        <video autoPlay muted loop className="background__video" ref={videoRef}>
          <source src="/media/bg-video.mp4" type="video/mp4" />
        </video>
        <img
          src="/media/screen.png"
          alt=""
          className="background__screen"
          ref={bgImageRef}
        />
      </div>

      <div className="film-grain" />
    </>
  );
}
