"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import type { AuthState } from "@/lib/types";

interface UseAuthReturn extends AuthState {
  loading: boolean;
  refetch: () => Promise<void>;
  logout: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState<AuthState>({
    authed: false,
    username: null,
    avatar_url: null,
    name: null,
  });

  const fetch = useCallback(async () => {
    try {
      const data = await api.auth.state();
      setState(data);
    } catch {
      setState({ authed: false, username: null, avatar_url: null, name: null });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const onFocus = () => fetch();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [fetch]);

  const logout = useCallback(async () => {
    await api.auth.logout();
    setState({ authed: false, username: null, avatar_url: null, name: null });
  }, []);

  return {
    loading,
    ...state,
    refetch: fetch,
    logout,
  };
}
