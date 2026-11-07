const API_BASE_URL =
  import.meta.env.VITE_API_URL || '/api';

class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

function getStoredSessionId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('guest_session_id') || sessionStorage.getItem('guest_session_id');
}

function setStoredSessionId(id: string) {
  if (typeof window === 'undefined' || !id) return;
  sessionStorage.setItem('guest_session_id', id);
  localStorage.setItem('guest_session_id', id);
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  // Attach session header fallback
  const storedSession = getStoredSessionId();
  if (storedSession && !headers.has('X-Session-ID')) {
    headers.set('X-Session-ID', storedSession);
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Guarantees HTTP-only cookie exchange
  });

  // Persist session identifier from response header
  const guestHeader = response.headers.get('x-guest-session-id');
  if (guestHeader) {
    setStoredSessionId(guestHeader);
  }

  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    const message = errorData.detail || errorData.message || `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, errorData);
  }

  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    const data = await response.json();
    // Only store if explicit guest_session_id is returned
    if (data && typeof data === 'object' && 'guest_session_id' in data && typeof data.guest_session_id === 'string') {
      setStoredSessionId(data.guest_session_id);
    }
    return data;
  }

  return response as unknown as T;
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, {
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  patch: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
  getBaseUrl: () => API_BASE_URL,
  clearLocalSession: () => {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('guest_session_id');
      localStorage.removeItem('guest_session_id');
    }
  },
};
