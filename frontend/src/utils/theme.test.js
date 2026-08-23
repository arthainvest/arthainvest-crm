import { applyTheme, getStoredTheme } from './theme';

const mockMatchMedia = (matches) => {
  window.matchMedia = jest.fn().mockImplementation((query) => ({
    matches,
    media: query,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  }));
};

describe('theme utils', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    mockMatchMedia(false);
  });

  test('getStoredTheme defaults to light when nothing is stored', () => {
    expect(getStoredTheme()).toBe('light');
  });

  test('getStoredTheme returns whatever was saved', () => {
    localStorage.setItem('theme', 'dark');
    expect(getStoredTheme()).toBe('dark');
  });

  test('applyTheme sets data-theme=dark for dark', () => {
    applyTheme('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  test('applyTheme sets data-theme=light for light', () => {
    applyTheme('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  test('applyTheme with auto resolves to light when system prefers light', () => {
    mockMatchMedia(false);
    applyTheme('auto');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  test('applyTheme with auto resolves to dark when system prefers dark', () => {
    mockMatchMedia(true);
    applyTheme('auto');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  test('applyTheme persists the raw preference (including "auto"), not just the resolved value', () => {
    applyTheme('auto');
    expect(localStorage.getItem('theme')).toBe('auto');
  });
});
