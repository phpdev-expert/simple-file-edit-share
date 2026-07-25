// Typed client for the FastAPI backend. All calls include the session cookie.

export interface User {
  id: number;
  email: string;
  name: string;
}

export interface DocSummary {
  id: number;
  title: string;
  owner: User;
  updated_at: string;
  role: string;
}

export interface DocDetail {
  id: number;
  title: string;
  content: string;
  owner: User;
  created_at: string;
  updated_at: string;
  role: string; // "owner" | "editor" | "viewer"
}

export interface Share {
  user: User;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// JWT is kept in memory + localStorage and sent as a Bearer token. The backend
// also accepts the same JWT via an HTTP-only cookie as a fallback.
const TOKEN_KEY = "ajaia_token";
let authToken: string | null = localStorage.getItem(TOKEN_KEY);

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
  const res = await fetch(`/api${path}`, {
    credentials: "include",
    ...options,
    headers,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function json(method: string, body?: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  };
}

export const api = {
  // --- auth ---
  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", json("POST", { email, password })),
  logout: () => request<{ ok: boolean }>("/auth/logout", json("POST")),
  me: () => request<User>("/auth/me"),

  // --- documents ---
  listDocuments: () => request<{ owned: DocSummary[]; shared: DocSummary[] }>("/documents"),
  createDocument: () => request<DocDetail>("/documents", json("POST")),
  getDocument: (id: number) => request<DocDetail>(`/documents/${id}`),
  updateDocument: (id: number, data: { title?: string; content?: string }) =>
    request<DocDetail>(`/documents/${id}`, json("PUT", data)),
  deleteDocument: (id: number) => request<void>(`/documents/${id}`, json("DELETE")),

  // --- sharing ---
  listShares: (id: number) => request<Share[]>(`/documents/${id}/shares`),
  addShare: (id: number, email: string, role: string) =>
    request<Share>(`/documents/${id}/shares`, json("POST", { email, role })),
  removeShare: (id: number, userId: number) =>
    request<void>(`/documents/${id}/shares/${userId}`, json("DELETE")),

  // --- upload ---
  importFile: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocDetail>("/uploads", { method: "POST", body: form });
  },
};
