"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  clearToken,
  getMe,
  getToken,
  login as loginRequest,
  register as registerRequest,
} from "@/services/auth";
import type { LoginPayload, RegisterPayload, User } from "@/types/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

export function useAuth() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const refreshUser = useCallback(async () => {
    const token = getToken();

    if (!token) {
      setUser(null);
      setStatus("unauthenticated");
      return null;
    }

    try {
      setStatus("loading");
      const currentUser = await getMe();
      setUser(currentUser);
      setStatus("authenticated");
      return currentUser;
    } catch {
      clearToken();
      setUser(null);
      setStatus("unauthenticated");
      return null;
    }
  }, []);

  useEffect(() => {
    // Auth state is bootstrapped from localStorage and then verified through /me.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    async (payload: LoginPayload, redirectTo = "/dashboard") => {
      await loginRequest(payload);
      await refreshUser();
      router.replace(redirectTo);
    },
    [refreshUser, router],
  );

  const register = useCallback(
    async (payload: RegisterPayload, redirectTo = "/dashboard") => {
      await registerRequest(payload);
      await login(payload, redirectTo);
    },
    [login],
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setStatus("unauthenticated");
    router.replace("/login");
  }, [router]);

  return {
    isAuthenticated: status === "authenticated",
    isLoading: status === "loading",
    login,
    logout,
    refreshUser,
    register,
    status,
    user,
  };
}
