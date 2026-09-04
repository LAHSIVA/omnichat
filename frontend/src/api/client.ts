import axios from "axios";

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

apiClient.interceptors.request.use((config) => {
  const accessToken = getAccessToken();

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

let isRefreshing = false;

let refreshSubscribers: Array<
  (accessToken: string) => void
> = [];

function subscribeToTokenRefresh(
  callback: (accessToken: string) => void,
): void {
  refreshSubscribers.push(callback);
}

function notifyTokenRefreshed(
  accessToken: string,
): void {
  refreshSubscribers.forEach((callback) => {
    callback(accessToken);
  });

  refreshSubscribers = [];
}

apiClient.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status !== 401 ||
      originalRequest?._retry
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
        subscribeToTokenRefresh((accessToken) => {
          originalRequest.headers.Authorization =
            `Bearer ${accessToken}`;

          apiClient(originalRequest)
            .then(resolve)
            .catch(reject);
        });
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

      setAccessToken(newAccessToken);

      notifyTokenRefreshed(newAccessToken);

      originalRequest.headers.Authorization =
        `Bearer ${newAccessToken}`;

      return apiClient(originalRequest);
    } catch (refreshError) {
      clearTokens();

      refreshSubscribers = [];

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export default apiClient;