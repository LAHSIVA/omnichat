import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  getAccessToken,
  getRefreshToken,
  setAccessToken,
  clearTokens,
} from "../features/auth/tokenStorage";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = getAccessToken();

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
);

let isRefreshing = false;

type RefreshSubscriber = {
  resolve: (accessToken: string) => void;
  reject: (error: unknown) => void;
};

let refreshSubscribers: RefreshSubscriber[] = [];

function subscribeToTokenRefresh(
  resolve: (accessToken: string) => void,
  reject: (error: unknown) => void,
): void {
  refreshSubscribers.push({
    resolve,
    reject,
  });
}

function notifyTokenRefreshed(
  accessToken: string,
): void {
  refreshSubscribers.forEach(({ resolve }) => {
    resolve(accessToken);
  });

  refreshSubscribers = [];
}

function notifyRefreshFailed(error: unknown): void {
  refreshSubscribers.forEach(({ reject }) => {
    reject(error);
  });

  refreshSubscribers = [];
}

function isRefreshRequest(
  config?: InternalAxiosRequestConfig,
): boolean {
  return Boolean(
    config?.url?.includes("/auth/token/refresh/"),
  );
}

apiClient.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const originalRequest =
      error.config as
        | (InternalAxiosRequestConfig & {
            _retry?: boolean;
          })
        | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isRefreshRequest(originalRequest)
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    const refreshToken = getRefreshToken();

    if (!refreshToken) {
      clearTokens();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        subscribeToTokenRefresh(
          (accessToken) => {
            originalRequest.headers.Authorization =
              `Bearer ${accessToken}`;

            apiClient(originalRequest)
              .then(resolve)
              .catch(reject);
          },
          reject,
        );
      });
    }

    isRefreshing = true;

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/auth/token/refresh/`,
        {
          refresh: refreshToken,
        },
      );

      const newAccessToken = response.data.access;

      if (!newAccessToken) {
        throw new Error(
          "Token refresh response did not contain an access token.",
        );
      }

      setAccessToken(newAccessToken);

      notifyTokenRefreshed(newAccessToken);

      originalRequest.headers.Authorization =
        `Bearer ${newAccessToken}`;

      return apiClient(originalRequest);
    } catch (refreshError) {
      clearTokens();

      notifyRefreshFailed(refreshError);

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export default apiClient;
