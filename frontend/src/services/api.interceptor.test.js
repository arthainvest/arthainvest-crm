// Regression test for the session-expiry fix: a 401 from an authenticated request must clear
// the stale session and redirect to /login?expired=1, instead of leaving every form to fail
// with its own generic, unexplained "Error creating X" alert (see git history for the bug).

let capturedErrorHandler;

jest.mock('axios', () => {
  const mockInstance = {
    interceptors: {
      response: {
        use: jest.fn((onSuccess, onError) => {
          capturedErrorHandler = onError;
        }),
      },
    },
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  };
  return {
    create: jest.fn(() => mockInstance),
  };
});

describe('api.js session-expiry interceptor', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    jest.resetModules();
    localStorage.clear();
    delete window.location;
    window.location = { ...originalLocation, href: '' };
  });

  afterAll(() => {
    window.location = originalLocation;
  });

  const loadInterceptor = () => {
    require('./api');
    return capturedErrorHandler;
  };

  test('a 401 on an authenticated request clears localStorage and redirects to /login?expired=1', async () => {
    localStorage.setItem('token', 'stale-token');
    localStorage.setItem('username', 'testuser');
    const onError = loadInterceptor();

    const error = {
      response: { status: 401 },
      config: { url: '/api/leads?token=stale-token' },
    };
    await expect(onError(error)).rejects.toEqual(error);

    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('username')).toBeNull();
    expect(window.location.href).toBe('/login?expired=1');
  });

  test('a 401 with no token present (nothing to expire) does not redirect', async () => {
    const onError = loadInterceptor();
    const error = { response: { status: 401 }, config: { url: '/api/leads' } };
    await expect(onError(error)).rejects.toEqual(error);
    expect(window.location.href).toBe('');
  });

  test('a 401 from the login endpoint itself (wrong password) does not redirect', async () => {
    const onError = loadInterceptor();
    const error = { response: { status: 401 }, config: { url: '/api/auth/login' } };
    await expect(onError(error)).rejects.toEqual(error);
    expect(window.location.href).toBe('');
  });

  test('a non-401 error passes through untouched', async () => {
    localStorage.setItem('token', 'still-valid');
    const onError = loadInterceptor();
    const error = { response: { status: 500 }, config: { url: '/api/leads' } };
    await expect(onError(error)).rejects.toEqual(error);
    expect(localStorage.getItem('token')).toBe('still-valid');
    expect(window.location.href).toBe('');
  });
});
