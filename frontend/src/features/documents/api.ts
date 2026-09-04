import apiClient from "../../api/client";

import type { Document } from "./types";

export async function getDocuments(): Promise<Document[]> {
  const response = await apiClient.get<Document[]>(
    "/knowledge/documents/",
  );

  return response.data;
}

export async function uploadDocument(
  title: string,
  file: File,
): Promise<Document> {
  const formData = new FormData();

  formData.append("title", title);
  formData.append("file", file);

  const response = await apiClient.post<Document>(
    "/knowledge/documents/",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return response.data;
}

export async function deleteDocument(
  documentId: number,
): Promise<void> {
  await apiClient.delete(
    `/knowledge/documents/${documentId}/`,
  );
}

export async function retryDocument(
  documentId: number,
): Promise<Document> {
  const response = await apiClient.post<Document>(
    `/knowledge/documents/${documentId}/retry/`,
  );

  return response.data;
}