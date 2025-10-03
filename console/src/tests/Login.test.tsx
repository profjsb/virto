import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login from '../Login';
import { api } from '../api';

vi.mock('../api', () => ({
  api: {
    post: vi.fn(),
  },
}));

describe('Login Component', () => {
  const mockOnAuthed = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders login form', () => {
    render(<Login onAuthed={mockOnAuthed} />);

    expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('has default email and password values', () => {
    render(<Login onAuthed={mockOnAuthed} />);

    const emailInput = screen.getByPlaceholderText('Email') as HTMLInputElement;
    const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement;

    expect(emailInput.value).toBe('admin@example.com');
    expect(passwordInput.value).toBe('admin123');
  });

  it('updates email and password on input change', async () => {
    const user = userEvent.setup();
    render(<Login onAuthed={mockOnAuthed} />);

    const emailInput = screen.getByPlaceholderText('Email');
    const passwordInput = screen.getByPlaceholderText('Password');

    await user.clear(emailInput);
    await user.type(emailInput, 'test@example.com');
    expect(emailInput).toHaveValue('test@example.com');

    await user.clear(passwordInput);
    await user.type(passwordInput, 'newpassword');
    expect(passwordInput).toHaveValue('newpassword');
  });

  it('handles successful login', async () => {
    const mockResponse = {
      data: {
        access_token: 'test-token-123',
        email: 'admin@example.com',
      },
    };

    vi.mocked(api.post).mockResolvedValueOnce(mockResponse);

    render(<Login onAuthed={mockOnAuthed} />);

    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'admin@example.com',
        password: 'admin123',
      });
      expect(localStorage.getItem('token')).toBe('test-token-123');
      expect(mockOnAuthed).toHaveBeenCalled();
    });
  });

  it('displays error message on failed login', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Unauthorized'));

    render(<Login onAuthed={mockOnAuthed} />);

    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByText('Login failed')).toBeInTheDocument();
      expect(mockOnAuthed).not.toHaveBeenCalled();
      expect(localStorage.getItem('token')).toBeNull();
    });
  });

  it('clears error message on new login attempt', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Unauthorized'));

    render(<Login onAuthed={mockOnAuthed} />);

    const loginButton = screen.getByRole('button', { name: /login/i });

    // First attempt - fails
    fireEvent.click(loginButton);
    await waitFor(() => {
      expect(screen.getByText('Login failed')).toBeInTheDocument();
    });

    // Second attempt
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { access_token: 'token' },
    });

    fireEvent.click(loginButton);
    await waitFor(() => {
      expect(screen.queryByText('Login failed')).not.toBeInTheDocument();
    });
  });
});
