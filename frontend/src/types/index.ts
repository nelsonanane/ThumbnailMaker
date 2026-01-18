/**
 * Type definitions for the Thumbnail Generator
 */

// ============================================
// API Response Types
// ============================================

export interface ThumbnailResponse {
  images: string[];
  prompt_used: string;
  thumbnail_text: string | null;
  generation_time_ms: number | null;
}

export interface VideoAnalysisResponse {
  video_id: string;
  title: string;
  description: string;
  tags: string[];
  channel: string;
  transcript: string | null;
}

export interface Template {
  id: string;
  name: string;
  category: string;
  description: string | null;
}

export interface FaceModel {
  id: string;
  name: string;
  trigger_word: string;
  status: 'pending' | 'training' | 'completed' | 'failed';
  lora_url: string | null;
  created_at: string;
}

// ============================================
// Request Types
// ============================================

export interface TextOverlayConfig {
  text?: string;
  position?: string;
  font_preset?: string;
  color_preset?: string;
  font_size?: number;
}

export interface ReferenceImage {
  data: string; // Base64 encoded image data
  description?: string; // Optional user-provided description
  preview?: string; // Preview URL for display (optional, client-side only)
}

export interface UploadedFacePhoto {
  data: string; // Base64 encoded image data
  name: string; // Original file name
  preview?: string; // Preview URL for display (optional, client-side only)
}

export interface FacePhotoForAPI {
  data: string; // Base64 encoded image data
  name: string; // Original file name for prompt labeling
}

export interface GenerateFromURLRequest {
  url: string;
  template_id?: string;
  face_model_id?: string;
  face_images?: FacePhotoForAPI[]; // Face photos with names for prompt labeling
  reference_thumbnails?: ReferenceImage[];
  num_variations?: number;
  add_text_overlay?: boolean;
  text_config?: TextOverlayConfig;
}

export interface GenerateFromPromptRequest {
  prompt: string;
  template_id?: string;
  face_model_id?: string;
  face_image_url?: string;
  face_images?: FacePhotoForAPI[]; // Face photos with names for prompt labeling
  reference_thumbnails?: ReferenceImage[];
  num_variations?: number;
  add_text_overlay?: boolean;
  thumbnail_text?: string;
  text_config?: TextOverlayConfig;
}

export interface TextOverlayRequest {
  image_data: string;
  text: string;
  position?: string;
  font_preset?: string;
  color_preset?: string;
  font_size?: number;
  add_gradient?: boolean;
}

export interface InpaintRequest {
  image_url: string;
  mask_url: string;
  prompt: string;
}

export interface TrainFaceModelRequest {
  name: string;
  images_zip_url: string;
}

// ============================================
// UI State Types
// ============================================

export type GenerationMode = 'url' | 'prompt';

export interface GenerationState {
  mode: GenerationMode;
  isGenerating: boolean;
  error: string | null;
  images: string[];
  promptUsed: string;
  thumbnailText: string;
}

export interface AppState extends GenerationState {
  // Input state
  videoUrl: string;
  customPrompt: string;
  selectedTemplate: string | null;
  selectedFaceModel: string | null;
  faceImageUrl: string | null;

  // Data
  templates: Template[];
  faceModels: FaceModel[];

  // Training state
  isTraining: boolean;
  trainingProgress: string;
}
