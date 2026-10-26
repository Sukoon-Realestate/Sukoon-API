import { isBackendEnabled, API_BASE_URL } from './config';
import { handleMockRequest } from './mockHandler';
import { BASE_PATH } from '../basePath';

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  params?: Record<string, string | number | boolean | undefined | null>;
  body?: any;
  anonymous?: boolean;
}

export async function apiClient<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  // Route to dummy static data JSON files when backend is disabled in env var
  if (!isBackendEnabled()) {
    return handleMockRequest<T>(endpoint, options);
  }
  const { params, headers, body, anonymous = false, ...restOptions } = options;

  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
  }

  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  // Bind rejection handling to the credential used by this exact request.
  let requestToken: string | null = null;
  // Attach Bearer token if present in localStorage
  if (!anonymous && typeof window !== 'undefined') {
    const token = localStorage.getItem('sukoon_access_token');
    requestToken = token;
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  let finalBody = body;
  if (body && typeof body !== 'string' && !(body instanceof FormData) && !(body instanceof Blob)) {
    finalBody = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      credentials: anonymous ? 'omit' : 'include',
      headers: {
        ...defaultHeaders,
        ...(headers as Record<string, string>),
      },
      body: finalBody,
      ...restOptions,
    });
  } catch {
    throw new Error('Connection interrupted. The result is unknown; refresh the original record before retrying.');
  }

  if (!anonymous && typeof window !== 'undefined' && localStorage.getItem('sukoon_access_token') !== requestToken) {
    throw new Error('Account session changed. Discard the previous response.');
  }

  if (!response.ok) {
    let errorData: any = null;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    const errorMessage = typeof errorData?.message === 'string' && errorData.message.trim()
      ? errorData.message : 'حدث خطأ في الاتصال بالخادم';

    if (!anonymous && response.status === 401 && !endpoint.includes('/auth/login/') &&
        typeof window !== 'undefined' && localStorage.getItem('sukoon_access_token') === requestToken) {
      if (typeof window !== 'undefined') {
        try {
          localStorage.removeItem('sukoon_access_token');
          localStorage.removeItem('sukoon_admin_auth');
          localStorage.removeItem('sukoon_user');
        } catch {}
        window.dispatchEvent(new Event('auth:unauthorized'));
        const loginPath = `${BASE_PATH}/login`;
        if (window.location.pathname !== loginPath) {
          window.location.href = loginPath;
        }
      }
    }

    throw new ApiError(response.status >= 500 ? 'Server outcome is unconfirmed. Refresh the original record before retrying.' : errorMessage, response.status);
  }

  const json: unknown = await response.json();
  if (!anonymous && typeof window !== 'undefined' && localStorage.getItem('sukoon_access_token') !== requestToken) {
    throw new Error('Account session changed. Discard the previous response.');
  }
  if (!json || typeof json !== 'object' || Array.isArray(json)) {
    throw new Error('Invalid API response');
  }
  const envelope = json as Record<string, unknown>;
  if (Object.keys(envelope).length !== 2 || typeof envelope.message !== 'string' ||
      !envelope.message.trim() || !('data' in envelope) ||
      (envelope.data !== null && typeof envelope.data !== 'object')) {
    throw new Error('Invalid API response');
  }
  // Keep the dashboard's typed page model while the HTTP body is an array.
  const pageHeaders = ['X-Page', 'X-Per-Page', 'X-Total-Count', 'X-Total-Pages', 'X-Next-Page', 'X-Previous-Page'];
  if (Array.isArray(envelope.data) && pageHeaders.some(name => response.headers.has(name))) {
    const integer = (name: string, minimum: number): number => {
      const raw = response.headers.get(name);
      if (raw === null || !/^\d+$/.test(raw) || !Number.isSafeInteger(Number(raw)) || Number(raw) < minimum) {
        throw new Error('Invalid API pagination');
      }
      return Number(raw);
    };
    const page = integer('X-Page', 1);
    const per_page = integer('X-Per-Page', 1);
    const total_pages = integer('X-Total-Pages', 1);
    const count = integer('X-Total-Count', 0);
    const next = response.headers.has('X-Next-Page') ? integer('X-Next-Page', 1) : null;
    const previous = response.headers.has('X-Previous-Page') ? integer('X-Previous-Page', 1) : null;
    if (page > total_pages || total_pages !== Math.max(1, Math.ceil(count / per_page)) ||
        envelope.data.length > per_page ||
        (next !== null && (next !== page + 1 || next > total_pages)) ||
        (previous !== null && previous !== page - 1)) {
      throw new Error('Invalid API pagination');
    }
    return { results: envelope.data, count, page, per_page, total_pages,
      next: next === null ? null : `?page=${next}`,
      previous: previous === null ? null : `?page=${previous}`,
    } as T;
  }
  return envelope.data as T;
}
