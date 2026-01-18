/**
 * Main application state store using Zustand
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  Template,
  FaceModel,
  GenerationMode,
  ReferenceImage,
  UploadedFacePhoto,
} from '@/types';
import api from '@/services/api';

interface ThumbnailState {
  // Mode
  mode: GenerationMode;
  setMode: (mode: GenerationMode) => void;

  // Input state
  videoUrl: string;
  setVideoUrl: (url: string) => void;

  customPrompt: string;
  setCustomPrompt: (prompt: string) => void;

  selectedTemplate: string | null;
  setSelectedTemplate: (id: string | null) => void;

  selectedFaceModel: string | null;
  setSelectedFaceModel: (id: string | null) => void;

  faceImageUrl: string | null;
  setFaceImageUrl: (url: string | null) => void;

  // Reference thumbnails
  referenceThumbnails: ReferenceImage[];
  addReferenceThumbnail: (image: ReferenceImage) => void;
  removeReferenceThumbnail: (index: number) => void;
  updateReferenceThumbnailDescription: (index: number, description: string) => void;
  clearReferenceThumbnails: () => void;

  // Face photos
  facePhotos: UploadedFacePhoto[];
  addFacePhoto: (photo: UploadedFacePhoto) => void;
  removeFacePhoto: (index: number) => void;
  clearFacePhotos: () => void;

  // Text overlay settings
  addTextOverlay: boolean;
  setAddTextOverlay: (add: boolean) => void;

  // Generation state
  isGenerating: boolean;
  generatedImages: string[];
  promptUsed: string;
  thumbnailText: string;
  generationError: string | null;

  // Data
  templates: Template[];
  faceModels: FaceModel[];

  // Training state
  isTraining: boolean;
  trainingProgress: string;

  // Actions
  loadTemplates: () => Promise<void>;
  loadFaceModels: () => Promise<void>;
  generateFromUrl: () => Promise<void>;
  generateFromPrompt: () => Promise<void>;
  trainFaceModel: (name: string, imagesZipUrl: string) => Promise<void>;
  clearGeneration: () => void;
}

export const useThumbnailStore = create<ThumbnailState>()(
  devtools(
    (set, get) => ({
      // Mode
      mode: 'url',
      setMode: (mode) => set({ mode }),

      // Input state
      videoUrl: '',
      setVideoUrl: (url) => {
        console.log('[Store] setVideoUrl:', url);
        set({ videoUrl: url });
      },

      customPrompt: '',
      setCustomPrompt: (prompt) => set({ customPrompt: prompt }),

      selectedTemplate: null,
      setSelectedTemplate: (id) => set({ selectedTemplate: id }),

      selectedFaceModel: null,
      setSelectedFaceModel: (id) => set({ selectedFaceModel: id }),

      faceImageUrl: null,
      setFaceImageUrl: (url) => set({ faceImageUrl: url }),

      // Reference thumbnails
      referenceThumbnails: [],
      addReferenceThumbnail: (image) => set((state) => ({
        referenceThumbnails: [...state.referenceThumbnails, image]
      })),
      removeReferenceThumbnail: (index) => set((state) => ({
        referenceThumbnails: state.referenceThumbnails.filter((_, i) => i !== index)
      })),
      updateReferenceThumbnailDescription: (index, description) => set((state) => ({
        referenceThumbnails: state.referenceThumbnails.map((img, i) =>
          i === index ? { ...img, description } : img
        )
      })),
      clearReferenceThumbnails: () => set({ referenceThumbnails: [] }),

      // Face photos
      facePhotos: [],
      addFacePhoto: (photo) => set((state) => ({
        facePhotos: [...state.facePhotos, photo]
      })),
      removeFacePhoto: (index) => set((state) => ({
        facePhotos: state.facePhotos.filter((_, i) => i !== index)
      })),
      clearFacePhotos: () => set({ facePhotos: [] }),

      // Text overlay settings
      addTextOverlay: true,
      setAddTextOverlay: (add) => set({ addTextOverlay: add }),

      // Generation state
      isGenerating: false,
      generatedImages: [],
      promptUsed: '',
      thumbnailText: '',
      generationError: null,

      // Data
      templates: [],
      faceModels: [],

      // Training state
      isTraining: false,
      trainingProgress: '',

      // Actions
      loadTemplates: async () => {
        try {
          const templates = await api.getTemplates();
          set({ templates });
        } catch (error) {
          console.error('Failed to load templates:', error);
        }
      },

      loadFaceModels: async () => {
        try {
          const faceModels = await api.listFaceModels();
          set({ faceModels });
        } catch (error) {
          console.error('Failed to load face models:', error);
        }
      },

      generateFromUrl: async () => {
        const { videoUrl, selectedTemplate, selectedFaceModel, addTextOverlay, referenceThumbnails, facePhotos } = get();

        console.log('[Store] generateFromUrl called with videoUrl:', videoUrl);

        if (!videoUrl) {
          set({ generationError: 'Please enter a YouTube URL' });
          return;
        }

        set({
          isGenerating: true,
          generationError: null,
          generatedImages: [],
        });

        try {
          // Prepare reference thumbnails for API (strip preview URLs)
          const referenceData = referenceThumbnails.length > 0
            ? referenceThumbnails.map(ref => ({ data: ref.data, description: ref.description }))
            : undefined;

          // Prepare face photos for API (extract base64 data)
          const faceImageData = facePhotos.length > 0
            ? facePhotos.map(photo => photo.data)
            : undefined;

          const response = await api.generateFromURL({
            url: videoUrl,
            template_id: selectedTemplate || undefined,
            face_model_id: selectedFaceModel || undefined,
            face_images: faceImageData,
            reference_thumbnails: referenceData,
            num_variations: 4,
            add_text_overlay: addTextOverlay,
          });

          set({
            generatedImages: response.images,
            promptUsed: response.prompt_used,
            thumbnailText: response.thumbnail_text || '',
            isGenerating: false,
          });
        } catch (error) {
          set({
            generationError: error instanceof Error ? error.message : 'Generation failed',
            isGenerating: false,
          });
        }
      },

      generateFromPrompt: async () => {
        const { customPrompt, selectedTemplate, selectedFaceModel, faceImageUrl, referenceThumbnails, facePhotos } = get();

        if (!customPrompt) {
          set({ generationError: 'Please enter a prompt' });
          return;
        }

        set({
          isGenerating: true,
          generationError: null,
          generatedImages: [],
        });

        try {
          // Prepare reference thumbnails for API (strip preview URLs)
          const referenceData = referenceThumbnails.length > 0
            ? referenceThumbnails.map(ref => ({ data: ref.data, description: ref.description }))
            : undefined;

          // Prepare face photos for API (extract base64 data)
          const faceImageData = facePhotos.length > 0
            ? facePhotos.map(photo => photo.data)
            : undefined;

          const response = await api.generateFromPrompt({
            prompt: customPrompt,
            template_id: selectedTemplate || undefined,
            face_model_id: selectedFaceModel || undefined,
            face_image_url: faceImageUrl || undefined,
            face_images: faceImageData,
            reference_thumbnails: referenceData,
            num_variations: 4,
          });

          set({
            generatedImages: response.images,
            promptUsed: response.prompt_used,
            thumbnailText: response.thumbnail_text || '',
            isGenerating: false,
          });
        } catch (error) {
          set({
            generationError: error instanceof Error ? error.message : 'Generation failed',
            isGenerating: false,
          });
        }
      },

      trainFaceModel: async (name: string, imagesZipUrl: string) => {
        set({ isTraining: true, trainingProgress: 'Starting training...' });

        try {
          await api.trainFaceModel({
            name,
            images_zip_url: imagesZipUrl,
          });

          set({
            trainingProgress: 'Training started. This will take 15-20 minutes.',
          });

          // Refresh face models list
          setTimeout(() => {
            get().loadFaceModels();
          }, 5000);
        } catch (error) {
          set({
            trainingProgress: error instanceof Error ? error.message : 'Training failed',
          });
        } finally {
          set({ isTraining: false });
        }
      },

      clearGeneration: () => {
        set({
          generatedImages: [],
          promptUsed: '',
          thumbnailText: '',
          generationError: null,
        });
      },
    }),
    {
      name: 'thumbnail-store',
    }
  )
);

export default useThumbnailStore;
