import axios from "axios";

export const TOKEN_STORAGE_KEY = "cme_access_token";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof window === "undefined") {
    return config;
  }

  const token = window.sessionStorage.getItem("learntrack_demo_token") ?? window.localStorage.getItem(TOKEN_STORAGE_KEY);

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(response => response, error => {
  if (typeof window !== "undefined" && error.response?.status === 401 && window.location.pathname.startsWith("/dashboard")) {
    if (sessionStorage.getItem("learntrack_demo_mode") === "true") {
      sessionStorage.removeItem("learntrack_demo_token");
      window.location.replace("/dashboard");
      return Promise.reject(error);
    }
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    for (const key of Object.keys(sessionStorage)) if (key.startsWith("cme-feedback:")) sessionStorage.removeItem(key);
    window.location.replace(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
  }
  return Promise.reject(error);
});
export default api;
