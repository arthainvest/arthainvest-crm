const STORAGE_KEY = 'theme';

const resolveTheme = (theme) => {
  if (theme === 'auto') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme === 'dark' ? 'dark' : 'light';
};

let mediaQuery = null;
let mediaListener = null;

export const applyTheme = (theme) => {
  document.documentElement.setAttribute('data-theme', resolveTheme(theme));
  localStorage.setItem(STORAGE_KEY, theme);

  if (mediaQuery && mediaListener) {
    mediaQuery.removeEventListener('change', mediaListener);
    mediaQuery = null;
    mediaListener = null;
  }

  if (theme === 'auto') {
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaListener = () => document.documentElement.setAttribute('data-theme', resolveTheme('auto'));
    mediaQuery.addEventListener('change', mediaListener);
  }
};

export const getStoredTheme = () => localStorage.getItem(STORAGE_KEY) || 'light';
