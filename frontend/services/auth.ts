import api, { TOKEN_STORAGE_KEY } from "@/services/api";
import type { AuthToken, LoginPayload, RegisterPayload, User } from "@/types/auth";

export async function register(payload: RegisterPayload) {
  const response = await api.post<User>("/register", payload);
  return response.data;
}

export async function login(payload: LoginPayload) {
  const response = await api.post<AuthToken>("/login", payload);
  setToken(response.data.access_token);
  return response.data;
}

export async function getMe() {
  const response = await api.get<User>("/me");
  return response.data;
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  }
}

export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function clearToken() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}
