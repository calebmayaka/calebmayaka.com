(function () {
    'use strict';
    const shell = document.querySelector('[data-home-shell]');
    if (!shell) return;

    const tablist = shell.querySelector('[data-home-tabs]');
    const tabs = Array.from(shell.querySelectorAll('[data-home-tab]'));
    const panels = Array.from(shell.querySelectorAll('[data-home-panel]'));
    const sidebar = shell.querySelector('[data-home-sidebar]');
    const strip = shell.querySelector('[data-home-strip]');
    const desktop = window.matchMedia('(min-width: 900px) and (min-height: 720px)');
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const validTabs = tabs.map((tab) => tab.dataset.homeTab);
    const tabFromHash = () => {
        const hash = window.location.hash.slice(1).toLowerCase();
        if (hash === 'inquiry') return 'contact';
        return validTabs.includes(hash) ? hash : null;
    };
    let active = shell.dataset.initialTab === 'contact' ? 'contact' : (tabFromHash() || 'work');

    function render() {
        document.body.classList.toggle('home-desktop', desktop.matches);
        shell.dataset.activeTab = active;
        if (desktop.matches) tablist.setAttribute('role', 'tablist');
        else tablist.removeAttribute('role');

        tabs.forEach((tab) => {
            const selected = tab.dataset.homeTab === active;
            tab.classList.toggle('is-active', selected);
            if (desktop.matches) {
                tab.setAttribute('role', 'tab');
                tab.setAttribute('aria-controls', tab.dataset.homeTab);
                tab.setAttribute('aria-selected', String(selected));
                tab.tabIndex = selected ? 0 : -1;
                tab.removeAttribute('aria-current');
            } else {
                tab.removeAttribute('role');
                tab.removeAttribute('aria-controls');
                tab.removeAttribute('aria-selected');
                tab.tabIndex = 0;
                if (selected) tab.setAttribute('aria-current', 'location');
                else tab.removeAttribute('aria-current');
            }
        });
        panels.forEach((panel) => {
            panel.hidden = desktop.matches && panel.dataset.homePanel !== active;
            panel.setAttribute('role', desktop.matches ? 'tabpanel' : 'region');
            panel.tabIndex = desktop.matches ? 0 : -1;
        });
        sidebar.hidden = desktop.matches && active !== 'work';
        strip.hidden = desktop.matches && active === 'work';
    }

    function scrollToPanel(name) {
        const panel = document.getElementById(name);
        const headerHeight = shell.querySelector('.home-header').getBoundingClientRect().height;
        window.scrollTo({
            top: window.scrollY + panel.getBoundingClientRect().top - headerHeight - 20,
            behavior: reduceMotion.matches ? 'auto' : 'smooth'
        });
    }

    function selectTab(name, updateHash, focusPanel) {
        if (!validTabs.includes(name)) return;
        active = name;
        if (updateHash && window.location.hash !== '#' + name) {
            window.history.pushState(null, '', '#' + name);
        }
        render();
        if (!desktop.matches) scrollToPanel(name);
        else if (focusPanel) document.getElementById(name).focus({ preventScroll: true });
    }

    tabs.forEach((tab, index) => {
        tab.addEventListener('click', (event) => {
            event.preventDefault();
            selectTab(tab.dataset.homeTab, true, false);
        });
        tab.addEventListener('keydown', (event) => {
            if (!desktop.matches) return;
            let next;
            if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
            else if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
            else if (event.key === 'Home') next = 0;
            else if (event.key === 'End') next = tabs.length - 1;
            else if (event.key === ' ') next = index;
            else return;
            event.preventDefault();
            selectTab(tabs[next].dataset.homeTab, true, false);
            tabs[next].focus();
        });
    });
    shell.querySelectorAll('[data-home-link]').forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            selectTab(link.dataset.homeLink, true, true);
        });
    });
    window.addEventListener('hashchange', () => {
        if (window.location.hash.toLowerCase() === '#inquiry') {
            window.history.replaceState(null, '', '#contact');
        }
        selectTab(tabFromHash() || 'work', false, false);
    });
    desktop.addEventListener('change', render);

    if (shell.dataset.initialTab === 'contact' || window.location.hash === '#inquiry') {
        window.history.replaceState(null, '', '#contact');
    }
    render();
    if (!desktop.matches && (tabFromHash() || shell.dataset.initialTab === 'contact')) {
        requestAnimationFrame(() => scrollToPanel(active));
    }

    const themeToggle = shell.querySelector('[data-home-theme]');
    const themeLabel = shell.querySelector('[data-home-theme-label]');
    function applyTheme(theme) {
        const dark = theme === 'dark';
        document.documentElement.classList.toggle('dark', dark);
        document.documentElement.classList.toggle('light', !dark);
        document.documentElement.style.colorScheme = theme;
        themeLabel.textContent = dark ? 'Dark' : 'Light';
        themeToggle.setAttribute('aria-pressed', String(dark));
        themeToggle.setAttribute('aria-label', 'Switch to ' + (dark ? 'light' : 'dark') + ' theme');
    }
    applyTheme(document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    themeToggle.addEventListener('click', () => {
        const theme = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
        applyTheme(theme);
        try {
            localStorage.setItem('cm-theme', theme);
            localStorage.setItem('portfolio-theme', theme);
        } catch (error) { /* Theme switching also works when storage is unavailable. */ }
    });
    window.addEventListener('storage', (event) => {
        if (['cm-theme', 'portfolio-theme'].includes(event.key) && ['light', 'dark'].includes(event.newValue)) {
            applyTheme(event.newValue);
        }
    });
})();
