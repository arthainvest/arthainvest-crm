import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Login from './Login';
import { loginUser } from '../services/api';

jest.mock('../services/api', () => ({
  loginUser: jest.fn(),
}));

const renderLogin = (onLoginSuccess = jest.fn()) =>
  render(
    <MemoryRouter>
      <Login onLoginSuccess={onLoginSuccess} />
    </MemoryRouter>
  );

describe('Login', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders username and password fields', () => {
    renderLogin();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  test('shows the session-expired message when redirected with ?expired=1', () => {
    render(
      <MemoryRouter initialEntries={['/login?expired=1']}>
        <Login onLoginSuccess={jest.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText(/session expired/i)).toBeInTheDocument();
  });

  test('does not show an error on a normal (non-expired) visit', () => {
    renderLogin();
    expect(screen.queryByText(/session expired/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/invalid credentials/i)).not.toBeInTheDocument();
  });

  test('successful login stores the token and calls onLoginSuccess', async () => {
    loginUser.mockResolvedValue({
      access_token: 'fake-token', user_id: 1, username: 'testuser', role: 'admin'
    });
    const onLoginSuccess = jest.fn();
    renderLogin(onLoginSuccess);

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: '12345' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => expect(onLoginSuccess).toHaveBeenCalled());
    expect(localStorage.getItem('token')).toBe('fake-token');
    expect(localStorage.getItem('username')).toBe('testuser');
  });

  test('failed login shows the backend error message and does not store a token', async () => {
    loginUser.mockRejectedValue({ response: { data: { detail: 'Invalid credentials' } } });
    renderLogin();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
    expect(localStorage.getItem('token')).toBeNull();
  });
});
