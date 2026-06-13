(function () {
    const root = document.documentElement;
    const themeToggle = document.querySelector('.theme-toggle');
    const siteNav = document.querySelector('.site-nav');
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    const progressLine = document.querySelector('.progress-line');
    const heroScene = document.querySelector('.hero-scene');
    const scrollCue = document.querySelector('.scroll-cue');
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const hasFinePointer = window.matchMedia('(pointer: fine)').matches;

    const getStoredTheme = () => {
        try {
            return localStorage.getItem('portfolio-theme');
        } catch (error) {
            return null;
        }
    };

    const storeTheme = (theme) => {
        try {
            localStorage.setItem('portfolio-theme', theme);
        } catch (error) {
            // Storage can fail in private contexts; the toggle should still work for this page.
        }
    };

    const THEMES = ['dark', 'light', 'ironman'];

    // ── Ironman particle state ─────────────────────────────────────
    let imParticleRaf = null;
    let imSparkRaf    = null;
    let imParticleCanvas = null;

    const initIronmanParticles = () => {
        if (reduceMotion) return;

        // ── Ambient full-page particle canvas ──────────────────────
        if (!imParticleCanvas) {
            imParticleCanvas = document.createElement('canvas');
            imParticleCanvas.id = 'im-particles';
            imParticleCanvas.style.cssText = 'position:fixed;inset:0;z-index:0;pointer-events:none;';
            document.body.prepend(imParticleCanvas);
        }
        const pctx = imParticleCanvas.getContext('2d');
        const COLORS = ['47,214,238', '75,140,255', '200,232,255'];
        let pw, ph, pdpr, pparticles;

        const pResize = () => {
            pdpr = Math.min(window.devicePixelRatio || 1, 2);
            pw = imParticleCanvas.width  = innerWidth  * pdpr;
            ph = imParticleCanvas.height = innerHeight * pdpr;
            imParticleCanvas.style.width  = innerWidth  + 'px';
            imParticleCanvas.style.height = innerHeight + 'px';
            const count = Math.min(90, Math.floor((innerWidth * innerHeight) / 22000));
            pparticles = Array.from({ length: count }, () => ({
                x: Math.random() * pw, y: Math.random() * ph,
                r: (Math.random() * 1.6 + 0.4) * pdpr,
                vx: (Math.random() - 0.5) * 0.18 * pdpr,
                vy: (Math.random() - 0.5) * 0.18 * pdpr - 0.04 * pdpr,
                a: Math.random() * 0.5 + 0.12,
                tw: Math.random() * Math.PI * 2,
                tws: Math.random() * 0.02 + 0.005,
                c: COLORS[(Math.random() * COLORS.length) | 0],
            }));
        };

        const pTick = () => {
            pctx.clearRect(0, 0, pw, ph);
            for (const p of pparticles) {
                p.x += p.vx; p.y += p.vy; p.tw += p.tws;
                if (p.x < -10) p.x = pw + 10;
                if (p.x > pw + 10) p.x = -10;
                if (p.y < -10) p.y = ph + 10;
                if (p.y > ph + 10) p.y = -10;
                const alpha = p.a * (0.55 + 0.45 * Math.sin(p.tw));
                pctx.beginPath();
                pctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                pctx.fillStyle = `rgba(${p.c},${alpha})`;
                pctx.shadowBlur = 8 * pdpr;
                pctx.shadowColor = `rgba(${p.c},${alpha})`;
                pctx.fill();
            }
            pctx.shadowBlur = 0;
            imParticleRaf = requestAnimationFrame(pTick);
        };

        pResize();
        window._imPResize = pResize;
        window.addEventListener('resize', pResize);
        pTick();

        // ── Hero sparks canvas ──────────────────────────────────────
        const sparkCanvas = document.querySelector('.im-hero-sparks');
        const heroEl = document.querySelector('.hero-scene');
        if (sparkCanvas && heroEl) {
            const sctx = sparkCanvas.getContext('2d');
            let sw, sh, sdpr, sparks;
            const SPARK_COLORS = ['255,150,70', '255,196,120', '255,228,170', '120,210,255', '47,214,238'];

            const spawnSpark = (seed) => {
                const cx = (0.42 + Math.random() * 0.46) * sw;
                const hot = Math.random() < 0.4;
                return {
                    x: cx + (Math.random() - 0.5) * 0.18 * sw,
                    y: seed ? Math.random() * sh : sh + Math.random() * 50 * sdpr,
                    r: (hot ? Math.random() * 0.7 + 0.3 : Math.random() * 1.2 + 0.5) * sdpr,
                    vy: -(Math.random() * 0.5 + 0.25) * sdpr,
                    sway: Math.random() * Math.PI * 2, swaySp: Math.random() * 0.03 + 0.01,
                    swayAmp: (Math.random() * 0.5 + 0.2) * sdpr,
                    life: 0, ttl: Math.random() * 320 + 200,
                    a: hot ? Math.random() * 0.45 + 0.55 : Math.random() * 0.45 + 0.25,
                    c: SPARK_COLORS[(Math.random() * SPARK_COLORS.length) | 0],
                };
            };

            const sResize = () => {
                sdpr = Math.min(window.devicePixelRatio || 1, 2);
                sw = sparkCanvas.width  = heroEl.clientWidth  * sdpr;
                sh = sparkCanvas.height = heroEl.clientHeight * sdpr;
                sparkCanvas.style.width  = heroEl.clientWidth  + 'px';
                sparkCanvas.style.height = heroEl.clientHeight + 'px';
                const n = Math.min(140, Math.floor(heroEl.clientWidth / 11));
                sparks = Array.from({ length: n }, () => spawnSpark(true));
            };

            const sTick = () => {
                sctx.clearRect(0, 0, sw, sh);
                if (window.scrollY < heroEl.clientHeight * 1.05) {
                    for (const e of sparks) {
                        e.life++; e.y += e.vy; e.sway += e.swaySp;
                        e.x += Math.cos(e.sway) * e.swayAmp; e.vy -= 0.0015 * sdpr;
                        if (e.y < -20 || e.life > e.ttl) Object.assign(e, spawnSpark(false));
                        const fadeIn  = Math.min(1, e.life / 40);
                        const fadeOut = Math.min(1, (e.ttl - e.life) / 70);
                        const flick   = 0.55 + 0.45 * Math.sin(e.life * 0.45);
                        const alpha   = e.a * fadeIn * fadeOut * flick;
                        sctx.beginPath();
                        sctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
                        sctx.fillStyle = `rgba(${e.c},${alpha})`;
                        sctx.shadowBlur = 12 * sdpr;
                        sctx.shadowColor = `rgba(${e.c},${alpha})`;
                        sctx.fill();
                    }
                }
                sctx.shadowBlur = 0;
                imSparkRaf = requestAnimationFrame(sTick);
            };

            sResize();
            window._imSResize = sResize;
            window.addEventListener('resize', sResize);
            sTick();
        }

        // ── Figure parallax (scroll + pointer) ─────────────────────
        const figInner = document.querySelector('.im-figure-inner');
        if (figInner && hasFinePointer) {
            let imRaf;
            window._imPointerMove = (ev) => {
                if (window.scrollY > window.innerHeight * 0.6) return;
                cancelAnimationFrame(imRaf);
                imRaf = requestAnimationFrame(() => {
                    const dx = (ev.clientX / window.innerWidth  - 0.5) * 16;
                    const dy = (ev.clientY / window.innerHeight - 0.5) * 12;
                    figInner.style.transform = `translate(${dx}px, ${dy}px)`;
                });
            };
            window.addEventListener('pointermove', window._imPointerMove);
        }
    };

    const destroyIronmanParticles = () => {
        if (imParticleRaf) { cancelAnimationFrame(imParticleRaf); imParticleRaf = null; }
        if (imSparkRaf)    { cancelAnimationFrame(imSparkRaf);    imSparkRaf    = null; }
        if (imParticleCanvas) {
            imParticleCanvas.remove();
            imParticleCanvas = null;
        }
        if (window._imPResize) { window.removeEventListener('resize', window._imPResize); window._imPResize = null; }
        if (window._imSResize) { window.removeEventListener('resize', window._imSResize); window._imSResize = null; }
        if (window._imPointerMove) { window.removeEventListener('pointermove', window._imPointerMove); window._imPointerMove = null; }
        const figInner = document.querySelector('.im-figure-inner');
        if (figInner) figInner.style.transform = '';
    };

    const setTheme = (theme) => {
        THEMES.forEach((t) => root.classList.remove(t));
        root.classList.add(theme);
        root.style.colorScheme = theme === 'light' ? 'light' : 'dark';

        if (themeToggle) {
            const labels = { dark: 'Switch to light mode', light: 'Switch to arc mode', ironman: 'Switch to dark mode' };
            themeToggle.setAttribute('aria-pressed', String(theme === 'light'));
            themeToggle.setAttribute('aria-label', labels[theme] || 'Toggle theme');
        }

        if (theme === 'ironman') initIronmanParticles();
        else destroyIronmanParticles();
    };

    setTheme(getStoredTheme() || 'ironman');

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = THEMES.find((t) => root.classList.contains(t)) || 'dark';
            const next = THEMES[(THEMES.indexOf(current) + 1) % THEMES.length];
            setTheme(next);
            storeTheme(next);
        });
    }

    const timeGreeting = document.querySelector('[data-time-greeting]');
    if (timeGreeting) {
        const hour = new Date().getHours();
        let greeting = 'Good day';
        if (hour >= 5 && hour < 12) {
            greeting = 'Good morning';
        } else if (hour >= 12 && hour < 18) {
            greeting = 'Good afternoon';
        } else if (hour >= 18 || hour < 5) {
            greeting = 'Good evening';
        }
        timeGreeting.textContent = greeting;
    }

    if (navToggle && navLinks) {
        const setMenuOpen = (isOpen) => {
            navLinks.classList.toggle('open', isOpen);
            navToggle.setAttribute('aria-expanded', String(isOpen));
            navToggle.setAttribute('aria-label', isOpen ? 'Close menu' : 'Open menu');
        };

        navToggle.addEventListener('click', () => {
            setMenuOpen(!navLinks.classList.contains('open'));
        });

        navLinks.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                setMenuOpen(false);
            });
        });

        document.addEventListener('click', (event) => {
            if (!navLinks.classList.contains('open')) return;
            if (siteNav && siteNav.contains(event.target)) return;
            setMenuOpen(false);
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && navLinks.classList.contains('open')) {
                setMenuOpen(false);
                navToggle.focus();
            }
        });
    }

    const updateNavState = () => {
        if (!siteNav) return;
        siteNav.classList.toggle('is-scrolled', (window.scrollY || document.documentElement.scrollTop) > 12);
    };

    updateNavState();
    window.addEventListener('scroll', updateNavState, { passive: true });

    const updateProgress = () => {
        if (!progressLine) return;
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        // Article-specific tracking is handled by blog.js on blog post pages.
        // Here we only manage the scroll cue; blog.js drives the bar itself.
        if (document.querySelector('article.blog-article')) {
            if (scrollCue) scrollCue.classList.toggle('is-hidden', scrollTop > 80);
            return;
        }
        const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
        const scale = maxScroll > 0 ? Math.min(scrollTop / maxScroll, 1) : 0;
        progressLine.style.transform = `scaleX(${scale})`;
        if (scrollCue) {
            scrollCue.classList.toggle('is-hidden', scrollTop > 80);
        }
    };

    updateProgress();

    // Ironman hero figure scroll parallax
    window.addEventListener('scroll', () => {
        if (!root.classList.contains('ironman') || reduceMotion) return;
        const figInner = document.querySelector('.im-figure-inner');
        if (figInner && window.scrollY < window.innerHeight) {
            figInner.style.transform = `translateY(${window.scrollY * 0.12}px) scale(${1 + window.scrollY * 0.00006})`;
        }
    }, { passive: true });

    window.addEventListener('scroll', updateProgress, { passive: true });

    if (heroScene && !reduceMotion && hasFinePointer) {
        let frame = null;
        const setHeroShift = (event) => {
            if (frame) cancelAnimationFrame(frame);
            frame = requestAnimationFrame(() => {
                const rect = heroScene.getBoundingClientRect();
                const x = ((event.clientX - rect.left) / rect.width - 0.5) * 24;
                const y = ((event.clientY - rect.top) / rect.height - 0.5) * 24;
                heroScene.style.setProperty('--hero-shift-x', `${x.toFixed(2)}px`);
                heroScene.style.setProperty('--hero-shift-y', `${y.toFixed(2)}px`);
            });
        };

        heroScene.addEventListener('pointermove', setHeroShift);
        heroScene.addEventListener('pointerleave', () => {
            heroScene.style.setProperty('--hero-shift-x', '0px');
            heroScene.style.setProperty('--hero-shift-y', '0px');
        });
    }

    if (heroScene && !reduceMotion && hasFinePointer) {
        heroScene.querySelectorAll('.btn').forEach((button) => {
            button.addEventListener('pointermove', (event) => {
                const rect = button.getBoundingClientRect();
                const x = event.clientX - rect.left;
                const y = event.clientY - rect.top;
                const magnetX = (x / rect.width - 0.5) * 10;
                const magnetY = (y / rect.height - 0.5) * 10;
                button.style.setProperty('--spot-x', `${x}px`);
                button.style.setProperty('--spot-y', `${y}px`);
                button.style.transform = `translate3d(${magnetX.toFixed(2)}px, ${magnetY.toFixed(2)}px, 0)`;
            });

            button.addEventListener('pointerleave', () => {
                button.style.setProperty('--spot-x', '50%');
                button.style.setProperty('--spot-y', '50%');
                button.style.removeProperty('transform');
            });
        });
    }

    if (!reduceMotion && hasFinePointer) {
        document.querySelectorAll('.bento-card').forEach((card) => {
            card.addEventListener('pointermove', (event) => {
                const rect = card.getBoundingClientRect();
                const x = event.clientX - rect.left;
                const y = event.clientY - rect.top;
                const rotateY = (x / rect.width - 0.5) * 8;
                const rotateX = (0.5 - y / rect.height) * 8;
                card.style.setProperty('--tilt-x', `${rotateX.toFixed(2)}deg`);
                card.style.setProperty('--tilt-y', `${rotateY.toFixed(2)}deg`);
                card.style.setProperty('--glare-x', `${x}px`);
                card.style.setProperty('--glare-y', `${y}px`);
            });

            card.addEventListener('pointerleave', () => {
                card.style.setProperty('--tilt-x', '0deg');
                card.style.setProperty('--tilt-y', '0deg');
                card.style.setProperty('--glare-x', '50%');
                card.style.setProperty('--glare-y', '50%');
            });
        });
    }

    const revealItems = document.querySelectorAll('.reveal');

    // Stagger siblings: reveals sharing a parent fade in 80ms apart (see --reveal-i in CSS)
    const staggerGroups = new Map();
    revealItems.forEach((item) => {
        const parent = item.parentElement;
        const index = staggerGroups.get(parent) || 0;
        item.style.setProperty('--reveal-i', String(Math.min(index, 7)));
        staggerGroups.set(parent, index + 1);
    });

    // Once the entrance finishes, drop the reveal classes so component hover
    // transitions (cards, buttons) are no longer overridden by the reveal one.
    const finishReveal = (item) => {
        const staggerIndex = Number(item.style.getPropertyValue('--reveal-i')) || 0;
        const settleMs = reduceMotion ? 0 : 720 + staggerIndex * 80 + 60;
        setTimeout(() => {
            item.classList.remove('reveal', 'is-visible');
            item.style.removeProperty('--reveal-i');
        }, settleMs);
    };

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                    finishReveal(entry.target);
                }
            });
        }, { threshold: 0.12 });

        revealItems.forEach((item) => observer.observe(item));
    } else {
        revealItems.forEach((item) => {
            item.classList.add('is-visible');
            finishReveal(item);
        });
    }

    const focusableSelector = [
        'a[href]',
        'button:not([disabled])',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])',
    ].join(',');
    let activeModal = null;
    let lastModalTrigger = null;

    const getFocusableItems = (container) => {
        return Array.from(container.querySelectorAll(focusableSelector))
            .filter((item) => item.offsetParent !== null || item === document.activeElement);
    };

    const openModal = (modal, trigger) => {
        if (!modal) return;
        activeModal = modal;
        lastModalTrigger = trigger || document.activeElement;
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('modal-lock');
        const firstFocusTarget = modal.querySelector('.modal-close') || getFocusableItems(modal)[0];
        if (firstFocusTarget) firstFocusTarget.focus();
    };

    const closeModal = (modal, shouldReturnFocus = true) => {
        if (!modal) return;
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-lock');
        if (activeModal === modal) activeModal = null;
        if (shouldReturnFocus && lastModalTrigger && typeof lastModalTrigger.focus === 'function') {
            lastModalTrigger.focus();
        }
    };

    document.querySelectorAll('.modal-open').forEach((button) => {
        button.addEventListener('click', () => {
            openModal(document.getElementById(button.dataset.modalTarget), button);
        });
    });

    document.querySelectorAll('.modal').forEach((modal) => {
        modal.addEventListener('click', (event) => {
            if (event.target === modal || event.target.classList.contains('modal-close')) {
                closeModal(modal);
            }
        });
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal.open').forEach((modal) => closeModal(modal));
        }

        if (event.key === 'Tab' && activeModal) {
            const focusableItems = getFocusableItems(activeModal);
            if (!focusableItems.length) return;
            const firstItem = focusableItems[0];
            const lastItem = focusableItems[focusableItems.length - 1];

            if (event.shiftKey && document.activeElement === firstItem) {
                event.preventDefault();
                lastItem.focus();
            } else if (!event.shiftKey && document.activeElement === lastItem) {
                event.preventDefault();
                firstItem.focus();
            }
        }
    });

    const snippetButtons = document.querySelectorAll('.snippet-card[data-snippet-id]');
    const codeTitle = document.getElementById('code-panel-title');
    const codeDescription = document.getElementById('code-panel-description');
    const codeTags = document.getElementById('code-panel-tags');
    const codeOutput = document.getElementById('code-panel-code');
    const codePanel = document.querySelector('.code-panel');

    const switchSnippet = (button) => {
        const template = document.getElementById(`snippet-${button.dataset.snippetId}-code`);
        if (!template || !codeTitle || !codeDescription || !codeTags || !codeOutput) return;
        if (button.classList.contains('active')) return;

        snippetButtons.forEach((item) => {
            item.classList.toggle('active', item === button);
            item.setAttribute('aria-selected', String(item === button));
        });
        if (codePanel && button.id) {
            codePanel.setAttribute('aria-labelledby', button.id);
        }

        if (codePanel && !reduceMotion) {
            codePanel.classList.remove('is-switching');
            void codePanel.offsetWidth;
            codePanel.classList.add('is-switching');
            setTimeout(() => codePanel.classList.remove('is-switching'), 420);
        }

        codeTitle.textContent = button.dataset.title || '';
        codeDescription.textContent = button.dataset.description || '';
        codeTags.innerHTML = '';
        (button.dataset.tags || '').split(',').filter(Boolean).forEach((tag) => {
            const tagElement = document.createElement('span');
            tagElement.textContent = tag.trim();
            codeTags.appendChild(tagElement);
        });
        codeOutput.innerHTML = template.innerHTML.trim();
    };

    snippetButtons.forEach((button) => {
        button.addEventListener('click', () => switchSnippet(button));
        button.addEventListener('keydown', (event) => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault();
            const buttons = Array.from(snippetButtons);
            const currentIndex = buttons.indexOf(button);
            let nextIndex = currentIndex;
            if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % buttons.length;
            if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + buttons.length) % buttons.length;
            if (event.key === 'Home') nextIndex = 0;
            if (event.key === 'End') nextIndex = buttons.length - 1;
            buttons[nextIndex].focus();
            switchSnippet(buttons[nextIndex]);
        });
    });

    document.querySelectorAll('.copy-code').forEach((button) => {
        button.addEventListener('click', async () => {
            const code = button.closest('.code-panel')?.querySelector('.showcase-code code')?.innerText;
            if (!code) return;

            try {
                await navigator.clipboard.writeText(code.replace(/^\s*\d+\s/gm, ''));
                button.classList.add('copied');
                setTimeout(() => button.classList.remove('copied'), 1200);
            } catch (error) {
                button.classList.remove('copied');
            }
        });
    });

    document.querySelectorAll('[data-copy-link]').forEach((button) => {
        button.addEventListener('click', async () => {
            const link = button.dataset.copyLink || window.location.href;
            try {
                await navigator.clipboard.writeText(link);
                button.classList.add('copied');
                setTimeout(() => button.classList.remove('copied'), 1200);
            } catch (error) {
                button.classList.remove('copied');
            }
        });
    });

    document.querySelectorAll('[data-copy-code]').forEach((button) => {
        button.addEventListener('click', async () => {
            const code = button.closest('.blog-code-block')?.querySelector('code')?.innerText;
            if (!code) return;

            try {
                await navigator.clipboard.writeText(code);
                button.classList.add('copied');
                button.textContent = 'Copied';
                setTimeout(() => {
                    button.classList.remove('copied');
                    button.textContent = 'Copy';
                }, 1200);
            } catch (error) {
                button.classList.remove('copied');
                button.textContent = 'Copy';
            }
        });
    });

    document.querySelectorAll('[data-share-link]').forEach((button) => {
        button.addEventListener('click', async () => {
            const shareData = {
                title: button.dataset.shareTitle || document.title,
                url: button.dataset.shareLink || window.location.href,
            };

            if (navigator.share) {
                try {
                    await navigator.share(shareData);
                    return;
                } catch (error) {
                    // Falling back to copy keeps the action useful if sharing is cancelled or unsupported.
                }
            }

            try {
                await navigator.clipboard.writeText(shareData.url);
                button.classList.add('copied');
                setTimeout(() => button.classList.remove('copied'), 1200);
            } catch (error) {
                button.classList.remove('copied');
            }
        });
    });

    document.querySelectorAll('[data-scroll-top]').forEach((button) => {
        button.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
        });
    });

    // ── Inquiry form — prevent double-submit & show loading state ────
    const inquiryForm = document.querySelector('.inquiry-form');
    if (inquiryForm) {
        const submitBtn = inquiryForm.querySelector('button[type="submit"]');
        inquiryForm.addEventListener('submit', () => {
            if (!submitBtn || submitBtn.disabled) return;
            submitBtn.disabled = true;
            submitBtn.dataset.originalText = submitBtn.textContent;
            submitBtn.textContent = 'Sending…';
            submitBtn.style.opacity = '0.72';
        });
        // Re-enable if the page stays (e.g. validation error scrolled back)
        window.addEventListener('pageshow', () => {
            if (submitBtn && submitBtn.disabled) {
                submitBtn.disabled = false;
                submitBtn.textContent = submitBtn.dataset.originalText || 'Send Inquiry';
                submitBtn.style.opacity = '';
            }
        });
    }

    // Wire aria-invalid + aria-describedby for form field errors
    document.querySelectorAll('.form-field').forEach((field) => {
        const errors = field.querySelector('.errorlist');
        const input = field.querySelector('input, select, textarea');
        if (errors && input) {
            const errorId = (input.id || input.name || Math.random().toString(36).slice(2)) + '-errors';
            errors.id = errorId;
            errors.setAttribute('role', 'alert');
            input.setAttribute('aria-invalid', 'true');
            input.setAttribute('aria-describedby', errorId);
        }
    });

    // ── Dashboard flash message auto-dismiss ──────────────────────
    document.querySelectorAll('[data-flash]').forEach((flash) => {
        const dismiss = () => {
            flash.style.transition = 'opacity 0.28s ease, transform 0.28s ease';
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-4px)';
            setTimeout(() => flash.remove(), 300);
        };

        const closeBtn = flash.querySelector('.dashboard-flash-close');
        if (closeBtn) closeBtn.addEventListener('click', dismiss);

        // Auto-dismiss after 4 s; keyboard users have the close button too
        const timer = setTimeout(dismiss, 4000);
        // Cancel auto-dismiss if the user hovers over the banner
        flash.addEventListener('mouseenter', () => clearTimeout(timer));
    });

    // ── Public site message auto-dismiss ──────────────────────────
    document.querySelectorAll('[data-site-message]').forEach((msg) => {
        const dismiss = () => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-6px)';
            setTimeout(() => {
                if (msg.parentElement) msg.remove();
            }, 320);
        };

        const closeBtn = msg.querySelector('.site-message-close');
        if (closeBtn) closeBtn.addEventListener('click', dismiss);

        // Auto-dismiss after 5 s; pause timer on hover so users can read it
        let timer = setTimeout(dismiss, 5000);
        msg.addEventListener('mouseenter', () => clearTimeout(timer));
        msg.addEventListener('mouseleave', () => { timer = setTimeout(dismiss, 2500); });
    });

    // ── Content list client-side filter ───────────────────────────
    document.querySelectorAll('.content-filter-input').forEach((input) => {
        const listId = input.dataset.filterTarget;
        const list = listId ? document.getElementById(listId) : null;
        if (!list) return;

        input.addEventListener('input', () => {
            const query = input.value.trim().toLowerCase();
            list.querySelectorAll('.content-list-row').forEach((row) => {
                const label = row.querySelector('.content-list-main strong')?.textContent.toLowerCase() || '';
                const secondary = row.querySelector('.content-list-main span')?.textContent.toLowerCase() || '';
                const matches = !query || label.includes(query) || secondary.includes(query);
                row.style.display = matches ? '' : 'none';
            });
        });
    });

    // ── Inline delete confirmation dialog ─────────────────────────
    const deleteDialog = document.getElementById('content-delete-dialog');
    const deleteForm   = document.getElementById('content-delete-form');
    const deleteLabel  = document.getElementById('content-delete-dialog-label');
    const deleteCancel = document.getElementById('content-delete-cancel');

    if (deleteDialog) {
        document.querySelectorAll('.content-delete-trigger').forEach((trigger) => {
            trigger.addEventListener('click', () => {
                if (deleteForm) deleteForm.action = trigger.dataset.deleteUrl || '';
                if (deleteLabel) {
                    const name = trigger.dataset.itemLabel || 'this item';
                    deleteLabel.textContent = `"${name}" — this action cannot be undone from the dashboard.`;
                }
                deleteDialog.showModal();
            });
        });

        if (deleteCancel) {
            deleteCancel.addEventListener('click', () => deleteDialog.close());
        }

        // Close on backdrop click
        deleteDialog.addEventListener('click', (event) => {
            if (event.target === deleteDialog) deleteDialog.close();
        });

        // Close on Escape (native for <dialog>, but keep explicit for clarity)
        deleteDialog.addEventListener('cancel', () => deleteDialog.close());
    }
})();
