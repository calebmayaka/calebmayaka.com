(function () {
    // ── Theme toggle (light / dark) ────────────────────────────────
    const root = document.documentElement;
    const themeToggle = document.querySelector('.theme-toggle');
    const applyTheme = (t) => {
        root.classList.remove('dark', 'light');
        root.classList.add(t);
        root.style.colorScheme = t;
        if (themeToggle) themeToggle.setAttribute('aria-pressed', String(t === 'light'));
    };
    let currentTheme = 'light';
    try {
        const stored = localStorage.getItem('portfolio-theme') || localStorage.getItem('cm-theme');
        if (stored === 'light' || stored === 'dark') currentTheme = stored;
    } catch (e) { /* private mode */ }
    applyTheme(currentTheme);
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            currentTheme = root.classList.contains('light') ? 'dark' : 'light';
            applyTheme(currentTheme);
            try {
                localStorage.setItem('portfolio-theme', currentTheme);
                localStorage.setItem('cm-theme', currentTheme);
            } catch (e) { /* ignore */ }
        });
    }

    const siteNav = document.querySelector('.site-nav');
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    const progressLine = document.querySelector('.progress-line');
    const heroScene = document.querySelector('.hero-scene');
    const scrollCue = document.querySelector('.scroll-cue');
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const hasFinePointer = window.matchMedia('(pointer: fine)').matches;

    // ── Blueprint hero: mouse parallax (grid + schematic) ──────────
    const bpHero = document.getElementById('bp-root');
    if (bpHero && !reduceMotion && hasFinePointer) {
        let bpRaf = null;
        const onMove = (event) => {
            const x = event.clientX / window.innerWidth - 0.5;
            const y = event.clientY / window.innerHeight - 0.5;
            if (bpRaf) cancelAnimationFrame(bpRaf);
            bpRaf = requestAnimationFrame(() => {
                bpHero.style.setProperty('--gx', (-x * 10).toFixed(1) + 'px');
                bpHero.style.setProperty('--gy', (-y * 10).toFixed(1) + 'px');
                bpHero.style.setProperty('--sx', (x * 30).toFixed(1) + 'px');
                bpHero.style.setProperty('--sy', (y * 30).toFixed(1) + 'px');
            });
        };
        window.addEventListener('mousemove', onMove, { passive: true });
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

    window.addEventListener('scroll', updateProgress, { passive: true });

    if (heroScene && !reduceMotion && hasFinePointer) {
        let frame = null;
        const setHeroShift = (event) => {
            if (frame) cancelAnimationFrame(frame);
            frame = requestAnimationFrame(() => {
                const rect = heroScene.getBoundingClientRect();
                const nx = (event.clientX - rect.left) / rect.width - 0.5;
                const ny = (event.clientY - rect.top) / rect.height - 0.5;
                heroScene.style.setProperty('--hero-shift-x', `${(nx * 24).toFixed(2)}px`);
                heroScene.style.setProperty('--hero-shift-y', `${(ny * 24).toFixed(2)}px`);
                // Unitless tilt for the 3D statement: lean toward the cursor.
                heroScene.style.setProperty('--hero-tilt-x', (ny * -9).toFixed(2));
                heroScene.style.setProperty('--hero-tilt-y', (nx * 12).toFixed(2));
            });
        };

        heroScene.addEventListener('pointermove', setHeroShift);
        heroScene.addEventListener('pointerleave', () => {
            heroScene.style.setProperty('--hero-shift-x', '0px');
            heroScene.style.setProperty('--hero-shift-y', '0px');
            heroScene.style.setProperty('--hero-tilt-x', '0');
            heroScene.style.setProperty('--hero-tilt-y', '0');
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
