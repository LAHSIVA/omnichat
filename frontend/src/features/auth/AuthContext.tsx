import {
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { useQueryClient } from "@tanstack/react-query";

import {
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
} from "./api";

import {
  clearTokens,
  getRefreshToken,
  getAccessToken,
  setTokens,
} from "./tokenStorage";

import type {
  CurrentUser,
  LoginRequest,
} from "./types";

import { AuthContext } from "./AuthContextValue";

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const queryClient = useQueryClient();

  const [user, setUser] = useState<CurrentUser | null>(
    null,
  );

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      const accessToken = getAccessToken();
      const refreshToken = getRefreshToken();

      if (!accessToken && !refreshToken) {
        if (isMounted) {
          setIsLoading(false);
        }

        return;
      }

      try {
        const currentUser = await getCurrentUser();

        if (isMounted) {
          setUser(currentUser);
        }
      } catch {
        /*
         * The API client already attempts an access-token
         * refresh when the current access token has expired.
         *
         * If we reach this point, the session could not
         * be restored. Treat it as a normal signed-out state.
         */
        clearTokens();

        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void restoreSession();

    return () => {
      isMounted = false;
    };
  }, []);

  async function login(
    data: LoginRequest,
  ): Promise<void> {
    const tokens = await loginRequest(data);

    setTokens(
      tokens.access,
      tokens.refresh,
    );

    const currentUser = await getCurrentUser();

    setUser(currentUser);
  }

  async function logout(): Promise<void> {
    const refreshToken = getRefreshToken();

    try {
      if (refreshToken) {
        await logoutRequest(refreshToken);
      }
    } finally {
      queryClient.clear();

      localStorage.removeItem(
        "omnichat_selected_conversation",
      );

      clearTokens();
      setUser(null);
    }
  }

  const value = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
