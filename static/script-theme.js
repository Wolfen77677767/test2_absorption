/* ================================================
   THEME SWITCHER - Dark/Light Mode Toggle
   ================================================ */

class ThemeSwitcher {
    constructor() {
        this.STORAGE_KEY = 'app-theme';
        this.DARK_MODE = 'dark-mode';
        this.LIGHT_MODE = 'light-mode';
        this.DEFAULT_THEME = this.DARK_MODE;

        this.init();
        window.addEventListener('storage', (event) => this.handleStorageChange(event));
    }

    init() {
        this.applyTheme(this.getSavedTheme());
        this.setupToggleButtons();
    }

    getSavedTheme() {
        const savedTheme = localStorage.getItem(this.STORAGE_KEY);
        return savedTheme === this.DARK_MODE || savedTheme === this.LIGHT_MODE
            ? savedTheme
            : this.DEFAULT_THEME;
    }

    getThemeColor(theme) {
        return theme === this.LIGHT_MODE ? '#eef4fa' : '#0a0e27';
    }

    setTheme(theme) {
        const nextTheme = theme === this.LIGHT_MODE ? this.LIGHT_MODE : this.DARK_MODE;
        localStorage.setItem(this.STORAGE_KEY, nextTheme);
        this.applyTheme(nextTheme);
    }

    applyTheme(theme) {
        const activeTheme = theme === this.LIGHT_MODE ? this.LIGHT_MODE : this.DARK_MODE;

        document.body.classList.remove(this.DARK_MODE, this.LIGHT_MODE);
        document.body.classList.add(activeTheme);
        document.documentElement.style.colorScheme = activeTheme === this.LIGHT_MODE ? 'light' : 'dark';

        this.updateMetaThemeColor(this.getThemeColor(activeTheme));
        this.updateToggleButtons(activeTheme);
        this.dispatchThemeChange(activeTheme);
    }

    updateMetaThemeColor(color) {
        let metaTheme = document.querySelector('meta[name="theme-color"]');
        if (!metaTheme) {
            metaTheme = document.createElement('meta');
            metaTheme.name = 'theme-color';
            document.head.appendChild(metaTheme);
        }
        metaTheme.content = color;
    }

    setupToggleButtons() {
        const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
        toggleButtons.forEach((button) => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                this.toggleTheme();
            });
        });
    }

    toggleTheme() {
        const currentTheme = this.getSavedTheme();
        const nextTheme = currentTheme === this.DARK_MODE ? this.LIGHT_MODE : this.DARK_MODE;
        this.setTheme(nextTheme);
    }

    updateToggleButtons(theme) {
        const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
        toggleButtons.forEach((button) => {
            const isDarkTheme = theme === this.DARK_MODE;
            const icon = button.querySelector('i');

            button.setAttribute('aria-pressed', String(isDarkTheme));
            button.title = isDarkTheme ? 'Switch to Light Mode' : 'Switch to Dark Mode';
            button.setAttribute('aria-label', button.title);

            if (icon) {
                icon.classList.remove('fa-sun', 'fa-moon');
                icon.classList.add(isDarkTheme ? 'fa-sun' : 'fa-moon');
            }
        });
    }

    dispatchThemeChange(theme) {
        document.dispatchEvent(new CustomEvent('themechange', {
            detail: { theme }
        }));
    }

    handleStorageChange(event) {
        if (event.key === this.STORAGE_KEY) {
            this.applyTheme(this.getSavedTheme());
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ThemeSwitcher());
} else {
    new ThemeSwitcher();
}
