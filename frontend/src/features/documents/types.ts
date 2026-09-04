export type DocumentStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export interface Document {
  id: number;
  title: string;
  file: string;
  original_filename: string;
  content_type: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}