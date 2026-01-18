/**
 * API client for the Thumbnail Generator backend
 */

import type {
  ThumbnailResponse,
  VideoAnalysisResponse,
  Template,
  FaceModel,
  GenerateFromURLRequest,
  GenerateFromPromptRequest,
  InpaintRequest,
  TextOverlayRequest,
  TrainFaceModelRequest,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ============================================
// Health & Info
// ============================================

export async function healthCheck(): Promise<{ status: string; version: string }> {
  return fetchAPI('/health');
}

// ============================================
// Templates
// ============================================

export async function getTemplates(): Promise<Template[]> {
  return fetchAPI('/templates');
}

export async function getTemplate(templateId: string): Promise<Template> {
  return fetchAPI(`/templates/${templateId}`);
}

// ============================================
// Video Analysis
// ============================================

export async function analyzeVideo(url: string): Promise<VideoAnalysisResponse> {
  return fetchAPI(`/analyze-video?url=${encodeURIComponent(url)}`);
}

// ============================================
// Generation
// ============================================

export async function generateFromURL(
  request: GenerateFromURLRequest
): Promise<ThumbnailResponse> {
  return fetchAPI('/generate/from-url', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function generateFromPrompt(
  request: GenerateFromPromptRequest
): Promise<ThumbnailResponse> {
  return fetchAPI('/generate/from-prompt', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function inpaintImage(
  request: InpaintRequest
): Promise<{ image_url: string; generation_time_ms: number }> {
  return fetchAPI('/inpaint', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function addTextOverlay(
  request: TextOverlayRequest
): Promise<{ image: string }> {
  return fetchAPI('/text-overlay', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// ============================================
// Face Models
// ============================================

export async function listFaceModels(): Promise<FaceModel[]> {
  return fetchAPI('/face-models');
}

export async function getFaceModel(modelId: string): Promise<FaceModel> {
  return fetchAPI(`/face-models/${modelId}`);
}

export async function trainFaceModel(
  request: TrainFaceModelRequest
): Promise<{ status: string; message: string }> {
  return fetchAPI('/face-models/train', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function deleteFaceModel(modelId: string): Promise<{ status: string }> {
  return fetchAPI(`/face-models/${modelId}`, {
    method: 'DELETE',
  });
}

// ============================================
// Export all functions
// ============================================

export const api = {
  healthCheck,
  getTemplates,
  getTemplate,
  analyzeVideo,
  generateFromURL,
  generateFromPrompt,
  inpaintImage,
  addTextOverlay,
  listFaceModels,
  getFaceModel,
  trainFaceModel,
  deleteFaceModel,
};

export default api;
