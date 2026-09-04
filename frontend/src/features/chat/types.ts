export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageSource {
  document_id: number;
  document_title: string;
  original_filename: string;
  chunk_index: number;
  distance: number | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  sources: MessageSource[];
}

export interface SendMessageRequest {
  content: string;
}

export interface ChatResponse {
  message: Message;
  sources: MessageSource[];
}