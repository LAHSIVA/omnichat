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
 * The model parameter is the UI model ID:
 *
 * auto
 * gemini-3.5-flash-lite
 * gemini-3.6-flash
 * claude-sonnet-4-5
 * fusion
 *
 * The backend accepts these IDs and routes all of them
 * to the configured actual provider model (gpt-4o-mini).
 */
export async function streamMessage(
  conversationId: string,
  content: string,
  onStatus: (status: StreamStatus) => void,
  onToken: (token: string) => void,
  onComplete: (data: ChatResponse) => void,
  onError: (error: Error) => void,
  model?: string,
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

          // IMPORTANT:
          // Send the UI model ID, NOT "gpt-4o-mini".
          //
          // If no model is supplied, use "auto", which is
          // accepted by the backend serializer.
          model: model || "auto",
        }),
      },
    );

    if (response.status === 401) {
      throw new Error(
        "Your session has expired. Please sign in again.",
      );
    }

    if (!response.ok) {
      let errorMessage = `Streaming request failed: ${response.status}`;

      try {
        const errorData = await response.json();

        if (errorData?.model?.[0]) {
          errorMessage = errorData.model[0];
        } else if (errorData?.detail) {
          errorMessage = errorData.detail;
        }
      } catch {
        // Keep the HTTP status error if the response
        // is not JSON.
      }

      throw new Error(errorMessage);
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

        let data: any;

        try {
          data = JSON.parse(
            dataLine.slice(6),
          );
        } catch {
          console.error(
            "Invalid SSE data:",
            dataLine,
          );
          continue;
        }

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
            data.message ||
              "The AI service failed.",
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
