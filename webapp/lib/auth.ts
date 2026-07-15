const TOKEN_KEY = "ink_token";
const AUTH_EVENT = "ink_auth_changed";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { ...extra };
  const t = getToken();
  if (t) h["Authorization"] = `Bearer ${t}`;
  return h;
}

export async function fetchCurrentUser<T = { user_id: number; username: string; created_at?: string }>(): Promise<T | null> {
  const res = await fetch("/api/auth/me", { headers: authHeaders() });
  if (res.status === 401 || res.status === 404) {
    if (getToken()) clearToken();
    return null;
  }
  if (!res.ok) return null;
  return res.json();
}

export function onAuthChanged(callback: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  const handleCustom = () => callback();
  const handleStorage = (event: StorageEvent) => {
    if (event.key === TOKEN_KEY) callback();
  };
  window.addEventListener(AUTH_EVENT, handleCustom);
  window.addEventListener("storage", handleStorage);
  return () => {
    window.removeEventListener(AUTH_EVENT, handleCustom);
    window.removeEventListener("storage", handleStorage);
  };
}
