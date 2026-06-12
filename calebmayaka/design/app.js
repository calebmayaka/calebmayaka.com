/* ============================================================
   Caleb Mayaka — Cinematic Portfolio
   Interaction layer: particles, nav, reveals, parallax
   ============================================================ */
(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Navbar scroll state + active link ---------- */
  const nav = document.querySelector(".nav");
  const onScroll = () => {
    if (window.scrollY > 30) nav.classList.add("scrolled");
    else nav.classList.remove("scrolled");
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* scroll-spy for nav links */
  const navLinks = [...document.querySelectorAll(".nav-links a[data-spy]")];
  const spyTargets = navLinks
    .map((a) => document.querySelector(a.getAttribute("href")))
    .filter(Boolean);
  if (spyTargets.length) {
    const spy = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const id = "#" + e.target.id;
            navLinks.forEach((a) =>
              a.classList.toggle("active", a.getAttribute("href") === id)
            );
          }
        });
      },
      { rootMargin: "-45% 0px -50% 0px" }
    );
    spyTargets.forEach((t) => spy.observe(t));
  }

  /* ---------- Scroll reveal ---------- */
  const reveals = document.querySelectorAll(".reveal");
  if (reduceMotion) {
    reveals.forEach((r) => r.classList.add("in"));
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    reveals.forEach((r) => io.observe(r));
  }

  /* ---------- Hero parallax (figure + content) ---------- */
  const figure = document.querySelector(".hero-figure");
  const heroContent = document.querySelector(".hero-content");
  if (!reduceMotion && figure) {
    let ticking = false;
    const applyParallax = () => {
      const y = window.scrollY;
      if (y < window.innerHeight) {
        figure.style.transform = `translateY(${y * 0.12}px) scale(${1 + y * 0.00006})`;
        if (heroContent) heroContent.style.transform = `translateY(${y * 0.22}px)`;
        if (heroContent) heroContent.style.opacity = String(Math.max(0, 1 - y / (window.innerHeight * 0.75)));
      }
      ticking = false;
    };
    window.addEventListener(
      "scroll",
      () => {
        if (!ticking) {
          requestAnimationFrame(applyParallax);
          ticking = true;
        }
      },
      { passive: true }
    );

    /* subtle pointer-driven drift on the figure */
    const figInner = figure.querySelector(".figure-inner");
    let raf;
    window.addEventListener("pointermove", (ev) => {
      if (window.scrollY > window.innerHeight * 0.6) return;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const dx = (ev.clientX / window.innerWidth - 0.5) * 16;
        const dy = (ev.clientY / window.innerHeight - 0.5) * 12;
        if (figInner) figInner.style.transform = `translate(${dx}px, ${dy}px)`;
      });
    });
  }

  /* ---------- Ambient particle field ---------- */
  const canvas = document.getElementById("particles");
  if (canvas && !reduceMotion) {
    const ctx = canvas.getContext("2d");
    let w, h, dpr, particles;

    const COLORS = ["47,214,238", "75,140,255", "200,232,255"];

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.width = innerWidth * dpr;
      h = canvas.height = innerHeight * dpr;
      canvas.style.width = innerWidth + "px";
      canvas.style.height = innerHeight + "px";
      const count = Math.min(90, Math.floor((innerWidth * innerHeight) / 22000));
      particles = Array.from({ length: count }, () => spawn());
    }
    function spawn() {
      return {
        x: Math.random() * w,
        y: Math.random() * h,
        r: (Math.random() * 1.6 + 0.4) * dpr,
        vx: (Math.random() - 0.5) * 0.18 * dpr,
        vy: (Math.random() - 0.5) * 0.18 * dpr - 0.04 * dpr,
        a: Math.random() * 0.5 + 0.12,
        tw: Math.random() * Math.PI * 2,
        tws: Math.random() * 0.02 + 0.005,
        c: COLORS[(Math.random() * COLORS.length) | 0],
      };
    }

    function tick() {
      ctx.clearRect(0, 0, w, h);
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.tw += p.tws;
        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;
        if (p.y < -10) p.y = h + 10;
        if (p.y > h + 10) p.y = -10;
        const alpha = p.a * (0.55 + 0.45 * Math.sin(p.tw));
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.c},${alpha})`;
        ctx.shadowBlur = 8 * dpr;
        ctx.shadowColor = `rgba(${p.c},${alpha})`;
        ctx.fill();
      }
      ctx.shadowBlur = 0;
      requestAnimationFrame(tick);
    }

    resize();
    window.addEventListener("resize", resize);
    tick();
  }

  /* ---------- Foreground hero sparks (rendered ON TOP of the figure) ---------- */
  const sparkCanvas = document.querySelector(".hero-sparks");
  const heroEl = document.querySelector(".hero");
  if (sparkCanvas && heroEl && !reduceMotion) {
    const sctx = sparkCanvas.getContext("2d");
    let sw, sh, sdpr, sparks;
    const SPARK_COLORS = ["255,150,70", "255,196,120", "255,228,170", "120,210,255", "47,214,238"];

    function spawnSpark(seed) {
      const cx = (0.42 + Math.random() * 0.46) * sw; // right-centre, over the figure
      const hot = Math.random() < 0.4;
      return {
        x: cx + (Math.random() - 0.5) * 0.18 * sw,
        y: seed ? Math.random() * sh : sh + Math.random() * 50 * sdpr,
        r: (hot ? Math.random() * 0.7 + 0.3 : Math.random() * 1.2 + 0.5) * sdpr,
        vy: -(Math.random() * 0.5 + 0.25) * sdpr,
        sway: Math.random() * Math.PI * 2,
        swaySp: Math.random() * 0.03 + 0.01,
        swayAmp: (Math.random() * 0.5 + 0.2) * sdpr,
        life: 0,
        ttl: Math.random() * 320 + 200,
        a: hot ? Math.random() * 0.45 + 0.55 : Math.random() * 0.45 + 0.25,
        c: SPARK_COLORS[(Math.random() * SPARK_COLORS.length) | 0],
      };
    }

    function sResize() {
      sdpr = Math.min(window.devicePixelRatio || 1, 2);
      sw = sparkCanvas.width = heroEl.clientWidth * sdpr;
      sh = sparkCanvas.height = heroEl.clientHeight * sdpr;
      sparkCanvas.style.width = heroEl.clientWidth + "px";
      sparkCanvas.style.height = heroEl.clientHeight + "px";
      const n = Math.min(140, Math.floor(heroEl.clientWidth / 11));
      sparks = Array.from({ length: n }, () => spawnSpark(true));
    }

    function sTick() {
      sctx.clearRect(0, 0, sw, sh);
      if (window.scrollY < heroEl.clientHeight * 1.05) {
        for (const e of sparks) {
          e.life++;
          e.y += e.vy;
          e.sway += e.swaySp;
          e.x += Math.cos(e.sway) * e.swayAmp;
          e.vy -= 0.0015 * sdpr;
          if (e.y < -20 || e.life > e.ttl) Object.assign(e, spawnSpark(false));
          const fadeIn = Math.min(1, e.life / 40);
          const fadeOut = Math.min(1, (e.ttl - e.life) / 70);
          const flick = 0.55 + 0.45 * Math.sin(e.life * 0.45);
          const alpha = e.a * fadeIn * fadeOut * flick;
          sctx.beginPath();
          sctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
          sctx.fillStyle = `rgba(${e.c},${alpha})`;
          sctx.shadowBlur = 12 * sdpr;
          sctx.shadowColor = `rgba(${e.c},${alpha})`;
          sctx.fill();
        }
      }
      sctx.shadowBlur = 0;
      requestAnimationFrame(sTick);
    }

    sResize();
    window.addEventListener("resize", sResize);
    sTick();
  }

  /* ---------- Magnetic / glow tilt on project cards ---------- */
  if (!reduceMotion) {
    document.querySelectorAll(".project-card").forEach((card) => {
      card.addEventListener("pointermove", (e) => {
        const r = card.getBoundingClientRect();
        const x = ((e.clientX - r.left) / r.width - 0.5) * 6;
        const y = ((e.clientY - r.top) / r.height - 0.5) * -6;
        card.style.transform = `translateY(-6px) rotateX(${y}deg) rotateY(${x}deg)`;
      });
      card.addEventListener("pointerleave", () => {
        card.style.transform = "";
      });
    });
  }

  /* ---------- Year ---------- */
  const yr = document.getElementById("year");
  if (yr) yr.textContent = new Date().getFullYear();
})();
