import apiClient from "../../api/client";

import type {
  ChatResponse,
  Conversation,
  Message,
  SendMessageRequest,
} from "./types";

export async function getConversations(): Promise<
  Conversation[]
> {
  const response = await apiClient.get<Conversation[]>(
    "/conversations/",
  );

  return response.data;
}

export async function createConversation(): Promise<Conversation> {
  const response = await apiClient.post<Conversation>(
    "/conversations/",
    {},
  );

  return response.data;
}

export async function getMessages(
  conversationId: string,
): Promise<Message[]> {
  const response = await apiClient.get<Message[]>(
    `/conversations/${conversationId}/messages/`,
  );

  return response.data;
}

export async function sendMessage(
  conversationId: string,
  data: SendMessageRequest,
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>(
    `/conversations/${conversationId}/messages/`,
    data,
  );

  return response.data;
}

export async function deleteConversation(
  conversationId: string,
): Promise<void> {
  await apiClient.delete(
    `/conversations/${conversationId}/`,
  );
}

/**
 * Represents a progress update sent by the backend
 * while an assistant response is being generated.
 */
export interface StreamStatus {
  stage:
    | "preparing"
    | "retrieving"
    | "retrieved"
    | "general"
    | "building_context"
    | "generating";

  message: string;
}

/**
 * Stream an assistant response using Server-Sent Events.
 *
 * The backend can send:
 *
 * - status → progress information
 * - token  → assistant response content
 * - done   → completed response
 * - error  → streaming error
 */
export async function streamMessage(
  conversationId: string,
  content: string,
  onStatus: (status: StreamStatus) => void,
  onToken: (token: string) => void,
  onComplete: (data: ChatResponse) => void,
  onError: (error: Error) => void,
): Promise<void> {
  const token = sessionStorage.getItem(
    "omnichat_access_token",
  );

  try {
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL}/conversations/${conversationId}/messages/stream/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : {}),
        },
        body: JSON.stringify({
          content,
        }),
      },
    );

    if (response.status === 401) {
      throw new Error(
        "Your session has expired. Please sign in again.",
      );
    }

    if (!response.ok) {
      throw new Error(
        `Streaming request failed: ${response.status}`,
      );
    }

    if (!response.body) {
      throw new Error(
        "Streaming response body is unavailable.",
      );
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, {
        stream: true,
      });

      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const event of events) {
        const dataLine = event
          .split("\n")
          .find((line) =>
            line.startsWith("data: "),
          );

        if (!dataLine) {
          continue;
        }

        const data = JSON.parse(
          dataLine.slice(6),
        );

        if (data.type === "status") {
          onStatus({
            stage: data.stage,
            message: data.message,
          });

          continue;
        }

        if (data.type === "token") {
          onToken(data.content);

          continue;
        }

        if (data.type === "done") {
          onComplete({
            message: data.message,
            sources: data.sources ?? [],
          });

          continue;
        }

        if (data.type === "error") {
          throw new Error(
            data.message || "Streaming failed.",
          );
        }
      }
    }
  } catch (error) {
    onError(
      error instanceof Error
        ? error
        : new Error(
            "An unexpected streaming error occurred.",
          ),
    );
  }
}
