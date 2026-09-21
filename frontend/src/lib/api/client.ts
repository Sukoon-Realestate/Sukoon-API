const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  params?: Record<string, string | number | boolean | undefined | null>;
  body?: any;
}

export async function apiClient<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, body, ...restOptions } = options;

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

  // Attach Bearer token if present in localStorage
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('sukoon_access_token');
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  let finalBody = body;
  if (body && typeof body !== 'string' && !(body instanceof FormData) && !(body instanceof Blob)) {
    finalBody = JSON.stringify(body);
  }

  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      ...defaultHeaders,
      ...(headers as Record<string, string>),
    },
    body: finalBody,
    ...restOptions,
  });

  if (!response.ok) {
    let errorData: any = null;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    const errorMessage =
      errorData?.message ||
      errorData?.detail ||
      (typeof errorData === 'object' ? JSON.stringify(errorData) : 'حدث خطأ في الاتصال بالخادم');

    if (response.status === 401 && !endpoint.includes('/auth/login/')) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('sukoon_access_token');
        localStorage.removeItem('sukoon_admin_auth');
        localStorage.removeItem('sukoon_user');
        window.dispatchEvent(new Event('auth:unauthorized'));
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }

    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return {} as T;
  }

  const json = await response.json();

  // ? GenericJsonRenderer wraps all responses: GET → {"data": payload}, others → {"message": "...", "data": payload}
  // Unwrap automatically so callers always receive the raw payload.
  if (
    json !== null &&
    typeof json === 'object' &&
    'data' in json &&
    Object.keys(json).every((k) => k === 'data' || k === 'message')
  ) {
    return json.data as T;
  }

  return json as T;
}
