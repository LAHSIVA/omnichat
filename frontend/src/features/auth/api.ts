import apiClient from "../../api/client";
import type {
  CurrentUser,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from "./types";

export async function login(
  data: LoginRequest,
): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>(
    "/auth/token/",
    data,
  );

  return response.data;
}

export async function register(
  data: RegisterRequest,
): Promise<void> {
  await apiClient.post(
    "/auth/register/",
    data,
  );
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiClient.get<CurrentUser>(
    "/auth/me/",
  );

  return response.data;
}

export async function refreshAccessToken(
  refresh: string,
): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>(
    "/auth/token/refresh/",
    { refresh },
  );

  return response.data;
}

export async function logout(
  refresh: string,
): Promise<void> {
  await apiClient.post(
    "/auth/logout/",
    { refresh },
  );
}