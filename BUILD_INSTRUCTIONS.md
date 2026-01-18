# AI Thumbnail Generator - Complete Build Instructions

This document contains step-by-step instructions to build an AI-powered YouTube thumbnail generator from scratch. These instructions can be given to any AI coding assistant to recreate the application.

---

## Project Overview

**What we're building:** A web application that generates professional YouTube thumbnails using AI. Users can:
- Paste a YouTube URL and get AI-generated thumbnails based on video content
- Write custom prompts for full creative control
- Upload reference thumbnails to match a specific style
- Upload MULTIPLE face photos with intelligent role assignment:
  - **First photo = Primary person** (main character, reactor, focal point)
  - **Additional photos = Secondary people** (replace other characters in reference thumbnails)
- Choose from pre-built style templates
- Get automatic text overlay on thumbnails
- Download generated thumbnails directly (works with base64 images)

**Tech Stack:**
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS, Zustand
- Backend: Python FastAPI
- AI: Google Gemini for image generation, OpenAI GPT-4o for prompt generation
- APIs: YouTube Data API, YouTube Transcript API

**Key Features:**
1. **Multi-Face Support**: Upload multiple face photos - AI analyzes EACH person individually and uses ALL of them in the generated thumbnail
2. **Reference Style Matching**: Upload existing thumbnails you like, AI extracts exact composition, colors, text style and replicates it
3. **Smart Download**: Proper file download for base64-encoded images (converts to blob and triggers download)

---

## STEP 1: Create Project Structure

Create the following folder structure:

```
ThumbnailMaker/
├── frontend/          # Next.js app
├── backend/           # Python FastAPI
├── README.md
└── BUILD_INSTRUCTIONS.md
```

---

## STEP 2: Setup Frontend

### 2.1 Initialize Next.js

```bash
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --use-npm
cd frontend
```

### 2.2 Install Dependencies

```bash
npm install zustand react-dropzone
```

### 2.3 Create Type Definitions

Create `frontend/src/types/index.ts`:

```typescript
export type GenerationMode = 'url' | 'prompt';

export interface Template {
  id: string;
  name: string;
  category: string;
  description?: string;
}

export interface FaceModel {
  id: string;
  name: string;
  trigger_word: string;
  status: string;
  lora_url?: string;
  created_at: string;
}

export interface ReferenceImage {
  data: string;        // base64 data
  preview: string;     // data URL for preview
  description?: string;
}

export interface UploadedFacePhoto {
  data: string;        // base64 data
  preview: string;     // data URL for preview
  name: string;
}

export interface ThumbnailResponse {
  images: string[];
  prompt_used: string;
  thumbnail_text?: string;
  generation_time_ms?: number;
}

export interface VideoURLRequest {
  url: string;
  template_id?: string;
  face_model_id?: string;
  face_images?: string[];
  reference_thumbnails?: { data: string; description?: string }[];
  num_variations?: number;
  add_text_overlay?: boolean;
}

export interface PromptRequest {
  prompt: string;
  template_id?: string;
  face_model_id?: string;
  face_image_url?: string;
  face_images?: string[];
  reference_thumbnails?: { data: string; description?: string }[];
  num_variations?: number;
}
```

### 2.4 Create API Service

Create `frontend/src/services/api.ts`:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface VideoURLRequest {
  url: string;
  template_id?: string;
  face_model_id?: string;
  face_images?: string[];
  reference_thumbnails?: { data: string; description?: string }[];
  num_variations?: number;
  add_text_overlay?: boolean;
}

interface PromptRequest {
  prompt: string;
  template_id?: string;
  face_model_id?: string;
  face_image_url?: string;
  face_images?: string[];
  reference_thumbnails?: { data: string; description?: string }[];
  num_variations?: number;
}

interface ThumbnailResponse {
  images: string[];
  prompt_used: string;
  thumbnail_text?: string;
}

interface Template {
  id: string;
  name: string;
  category: string;
}

const api = {
  async getTemplates(): Promise<Template[]> {
    const response = await fetch(`${API_URL}/templates`);
    if (!response.ok) throw new Error('Failed to fetch templates');
    return response.json();
  },

  async generateFromURL(request: VideoURLRequest): Promise<ThumbnailResponse> {
    const response = await fetch(`${API_URL}/generate/from-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Generation failed');
    }
    return response.json();
  },

  async generateFromPrompt(request: PromptRequest): Promise<ThumbnailResponse> {
    const response = await fetch(`${API_URL}/generate/from-prompt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Generation failed');
    }
    return response.json();
  },

  async listFaceModels() {
    const response = await fetch(`${API_URL}/face-models`);
    if (!response.ok) throw new Error('Failed to fetch face models');
    return response.json();
  },

  async trainFaceModel(request: { name: string; images_zip_url: string }) {
    const response = await fetch(`${API_URL}/face-models/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to start training');
    return response.json();
  },
};

export default api;
```

### 2.5 Create Zustand Store

Create `frontend/src/stores/thumbnailStore.ts`:

```typescript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import api from '@/services/api';

type GenerationMode = 'url' | 'prompt';

interface Template {
  id: string;
  name: string;
  category: string;
}

interface ReferenceImage {
  data: string;
  preview: string;
  description?: string;
}

interface UploadedFacePhoto {
  data: string;
  preview: string;
  name: string;
}

interface ThumbnailState {
  // Mode
  mode: GenerationMode;
  setMode: (mode: GenerationMode) => void;

  // Inputs
  videoUrl: string;
  setVideoUrl: (url: string) => void;
  customPrompt: string;
  setCustomPrompt: (prompt: string) => void;
  selectedTemplate: string | null;
  setSelectedTemplate: (id: string | null) => void;

  // Reference images
  referenceThumbnails: ReferenceImage[];
  addReferenceThumbnail: (image: ReferenceImage) => void;
  removeReferenceThumbnail: (index: number) => void;
  clearReferenceThumbnails: () => void;

  // Face photos
  facePhotos: UploadedFacePhoto[];
  addFacePhoto: (photo: UploadedFacePhoto) => void;
  removeFacePhoto: (index: number) => void;
  clearFacePhotos: () => void;

  // Text overlay
  addTextOverlay: boolean;
  setAddTextOverlay: (add: boolean) => void;

  // Generation state
  isGenerating: boolean;
  generatedImages: string[];
  promptUsed: string;
  thumbnailText: string;
  generationError: string | null;

  // Templates
  templates: Template[];
  loadTemplates: () => Promise<void>;

  // Actions
  generateFromUrl: () => Promise<void>;
  generateFromPrompt: () => Promise<void>;
  clearGeneration: () => void;
}

export const useThumbnailStore = create<ThumbnailState>()(
  devtools((set, get) => ({
    mode: 'url',
    setMode: (mode) => set({ mode }),

    videoUrl: '',
    setVideoUrl: (url) => set({ videoUrl: url }),
    customPrompt: '',
    setCustomPrompt: (prompt) => set({ customPrompt: prompt }),
    selectedTemplate: null,
    setSelectedTemplate: (id) => set({ selectedTemplate: id }),

    referenceThumbnails: [],
    addReferenceThumbnail: (image) => set((state) => ({
      referenceThumbnails: [...state.referenceThumbnails, image]
    })),
    removeReferenceThumbnail: (index) => set((state) => ({
      referenceThumbnails: state.referenceThumbnails.filter((_, i) => i !== index)
    })),
    clearReferenceThumbnails: () => set({ referenceThumbnails: [] }),

    facePhotos: [],
    addFacePhoto: (photo) => set((state) => ({
      facePhotos: [...state.facePhotos, photo]
    })),
    removeFacePhoto: (index) => set((state) => ({
      facePhotos: state.facePhotos.filter((_, i) => i !== index)
    })),
    clearFacePhotos: () => set({ facePhotos: [] }),

    addTextOverlay: true,
    setAddTextOverlay: (add) => set({ addTextOverlay: add }),

    isGenerating: false,
    generatedImages: [],
    promptUsed: '',
    thumbnailText: '',
    generationError: null,

    templates: [],

    loadTemplates: async () => {
      try {
        const templates = await api.getTemplates();
        set({ templates });
      } catch (error) {
        console.error('Failed to load templates:', error);
      }
    },

    generateFromUrl: async () => {
      const { videoUrl, selectedTemplate, addTextOverlay, referenceThumbnails, facePhotos } = get();
      if (!videoUrl) {
        set({ generationError: 'Please enter a YouTube URL' });
        return;
      }

      set({ isGenerating: true, generationError: null, generatedImages: [] });

      try {
        const response = await api.generateFromURL({
          url: videoUrl,
          template_id: selectedTemplate || undefined,
          face_images: facePhotos.length > 0 ? facePhotos.map(p => p.data) : undefined,
          reference_thumbnails: referenceThumbnails.length > 0
            ? referenceThumbnails.map(r => ({ data: r.data, description: r.description }))
            : undefined,
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
      const { customPrompt, selectedTemplate, referenceThumbnails, facePhotos } = get();
      if (!customPrompt) {
        set({ generationError: 'Please enter a prompt' });
        return;
      }

      set({ isGenerating: true, generationError: null, generatedImages: [] });

      try {
        const response = await api.generateFromPrompt({
          prompt: customPrompt,
          template_id: selectedTemplate || undefined,
          face_images: facePhotos.length > 0 ? facePhotos.map(p => p.data) : undefined,
          reference_thumbnails: referenceThumbnails.length > 0
            ? referenceThumbnails.map(r => ({ data: r.data, description: r.description }))
            : undefined,
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

    clearGeneration: () => set({
      generatedImages: [],
      promptUsed: '',
      thumbnailText: '',
      generationError: null,
    }),
  }))
);

export default useThumbnailStore;
```

### 2.6 Create Reference Image Uploader Component

Create `frontend/src/components/ReferenceImageUploader.tsx`:

```typescript
'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useThumbnailStore } from '@/stores/thumbnailStore';

export function ReferenceImageUploader() {
  const { referenceThumbnails, addReferenceThumbnail, removeReferenceThumbnail } = useThumbnailStore();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result as string;
        addReferenceThumbnail({
          data: base64.split(',')[1], // Remove data URL prefix for API
          preview: base64,
          description: '',
        });
      };
      reader.readAsDataURL(file);
    });
  }, [addReferenceThumbnail]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] },
    maxFiles: 3,
  });

  return (
    <div>
      <h3 className="mb-3 text-sm font-medium text-gray-300">
        Reference Thumbnails (Optional)
      </h3>
      <p className="mb-3 text-xs text-gray-500">
        Upload thumbnails you like to match their style
      </p>

      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-4 text-center transition-colors ${
          isDragActive
            ? 'border-purple-500 bg-purple-500/10'
            : 'border-gray-600 hover:border-gray-500'
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-sm text-gray-400">
          {isDragActive ? 'Drop images here' : 'Drag & drop or click to upload'}
        </p>
      </div>

      {referenceThumbnails.length > 0 && (
        <div className="mt-4 grid grid-cols-3 gap-2">
          {referenceThumbnails.map((img, index) => (
            <div key={index} className="relative aspect-video">
              <img
                src={img.preview}
                alt={`Reference ${index + 1}`}
                className="h-full w-full rounded object-cover"
              />
              <button
                onClick={() => removeReferenceThumbnail(index)}
                className="absolute -right-1 -top-1 rounded-full bg-red-500 p-1 text-white hover:bg-red-600"
              >
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 2.7 Create Face Photo Uploader Component

Create `frontend/src/components/FacePhotoUploader.tsx`:

```typescript
'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useThumbnailStore } from '@/stores/thumbnailStore';

export function FacePhotoUploader() {
  const { facePhotos, addFacePhoto, removeFacePhoto } = useThumbnailStore();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result as string;
        addFacePhoto({
          data: base64.split(',')[1],
          preview: base64,
          name: file.name,
        });
      };
      reader.readAsDataURL(file);
    });
  }, [addFacePhoto]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] },
    maxFiles: 5,
  });

  return (
    <div>
      <h3 className="mb-3 text-sm font-medium text-gray-300">
        Face Photos (Optional)
      </h3>
      <p className="mb-3 text-xs text-gray-500">
        Upload photos of your face to include in thumbnails
      </p>

      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-4 text-center transition-colors ${
          isDragActive
            ? 'border-purple-500 bg-purple-500/10'
            : 'border-gray-600 hover:border-gray-500'
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-sm text-gray-400">
          {isDragActive ? 'Drop photos here' : 'Drag & drop or click to upload'}
        </p>
      </div>

      {facePhotos.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {facePhotos.map((photo, index) => (
            <div key={index} className="relative h-16 w-16">
              <img
                src={photo.preview}
                alt={photo.name}
                className="h-full w-full rounded-full object-cover"
              />
              <button
                onClick={() => removeFacePhoto(index)}
                className="absolute -right-1 -top-1 rounded-full bg-red-500 p-1 text-white hover:bg-red-600"
              >
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 2.8 Create Component Index

Create `frontend/src/components/index.ts`:

```typescript
export { ReferenceImageUploader } from './ReferenceImageUploader';
export { FacePhotoUploader } from './FacePhotoUploader';
```

### 2.9 Create Main Page

Replace `frontend/src/app/page.tsx` with the main application UI that includes:
- Mode toggle (URL vs Prompt)
- YouTube URL input or Prompt textarea
- Template selector grid
- Reference image uploader
- Face photo uploader
- Text overlay toggle
- Generate button with loading state
- Results gallery with download option
- Error display

The page should use the Zustand store for all state management and call the appropriate generate function based on mode.

### 2.10 Create Environment File

Create `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## STEP 3: Setup Backend

### 3.1 Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3.2 Create Requirements File

Create `backend/requirements.txt`:

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-multipart==0.0.20
openai==1.59.7
google-genai==1.0.0
Pillow==11.1.0
youtube-transcript-api==1.2.3
google-api-python-client==2.159.0
python-dotenv==1.0.1
pydantic==2.10.5
pydantic-settings==2.7.1
httpx==0.28.1
```

Install: `pip install -r requirements.txt`

### 3.3 Create Config

Create `backend/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os

class Settings(BaseSettings):
    app_name: str = "Thumbnail Generator API"
    debug: bool = False
    api_version: str = "v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # AI Services
    openai_api_key: str = ""
    google_ai_api_key: str = ""
    youtube_api_key: str = ""

    # Optional
    supabase_url: str = ""
    supabase_service_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

if settings.google_ai_api_key:
    os.environ["GOOGLE_AI_API_KEY"] = settings.google_ai_api_key
```

### 3.4 Create Pydantic Models

Create `backend/models.py`:

```python
from pydantic import BaseModel
from typing import Optional, List

class ReferenceImageData(BaseModel):
    data: str  # base64 image data
    description: Optional[str] = None

class VideoURLRequest(BaseModel):
    url: str
    template_id: Optional[str] = None
    face_model_id: Optional[str] = None
    face_images: Optional[List[str]] = None
    reference_thumbnails: Optional[List[ReferenceImageData]] = None
    num_variations: int = 4
    add_text_overlay: bool = True

class PromptRequest(BaseModel):
    prompt: str
    template_id: Optional[str] = None
    face_model_id: Optional[str] = None
    face_image_url: Optional[str] = None
    face_images: Optional[List[str]] = None
    reference_thumbnails: Optional[List[ReferenceImageData]] = None
    num_variations: int = 4
    thumbnail_text: Optional[str] = None
    add_text_overlay: bool = False

class ThumbnailResponse(BaseModel):
    images: List[str]
    prompt_used: str
    thumbnail_text: Optional[str] = None
    generation_time_ms: Optional[int] = None

class TemplateResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
```

### 3.5 Create Video Analyzer Service

Create `backend/services/video_analyzer.py`:

```python
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import re

class VideoAnalyzer:
    def __init__(self, youtube_api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)

    def extract_video_id(self, url: str) -> str:
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError("Invalid YouTube URL")

    def get_metadata(self, video_id: str) -> dict:
        request = self.youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        )
        response = request.execute()

        if not response['items']:
            raise ValueError("Video not found")

        snippet = response['items'][0]['snippet']
        return {
            'title': snippet.get('title'),
            'description': snippet.get('description', '')[:1000],
            'tags': snippet.get('tags', []),
            'channel': snippet.get('channelTitle'),
        }

    def get_transcript(self, video_id: str) -> str:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            fetched = transcript.fetch()
            full_text = ' '.join([entry['text'] for entry in fetched])
            return full_text[:5000]
        except Exception:
            return ""

    def analyze(self, url: str) -> dict:
        video_id = self.extract_video_id(url)
        metadata = self.get_metadata(video_id)
        transcript = self.get_transcript(video_id)

        return {
            'video_id': video_id,
            **metadata,
            'transcript': transcript,
        }
```

### 3.6 Create Prompt Generator Service

Create `backend/services/prompt_generator.py`:

```python
import openai
import json
from typing import Optional

SYSTEM_PROMPT = """You are a YouTube Thumbnail Architect specializing in viral, high-CTR thumbnail designs.

Your task: Analyze the video content and generate a detailed image prompt for AI image generation.

RULES:
1. SUBJECT: Describe the main subject with vivid details. If a person should appear, describe their expression (shocked, excited, skeptical).
2. COMPOSITION: Use proven layouts - split screen, close-up face on right, object on left, or centered dramatic pose.
3. TEXT: Include SHORT punchy text (2-4 words max) that creates curiosity. This will be overlaid separately.
4. LIGHTING: Always specify dramatic lighting - rim light, volumetric, god rays, studio softbox.
5. STYLE: Include quality tokens - 4k, hyper-realistic, sharp focus, vibrant colors, YouTube thumbnail style.
6. BACKGROUND: Describe a relevant, slightly blurred background that adds context.

OUTPUT FORMAT:
Return ONLY a JSON object with these fields:
{
    "prompt": "The complete image generation prompt (DO NOT include text in the image itself)",
    "thumbnail_text": "The 2-4 word text overlay to add separately",
    "emotion": "The primary emotion to convey",
    "composition": "Brief description of the layout"
}"""

class PromptGenerator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def generate_prompt(
        self,
        video_data: dict,
        template_system_prompt: Optional[str] = None,
        trigger_word: str = "person",
        reference_analysis: Optional[dict] = None,
        face_description: Optional[str] = None,
    ) -> dict:
        system = template_system_prompt or SYSTEM_PROMPT

        # Add reference style guidance if available
        if reference_analysis:
            system += f"\n\nMATCH THIS STYLE: {json.dumps(reference_analysis)}"

        # Add face description if available
        if face_description:
            system += f"\n\nINCLUDE THIS PERSON: {face_description}"

        user_content = f"""
VIDEO TITLE: {video_data.get('title', 'Unknown')}

VIDEO DESCRIPTION: {video_data.get('description', 'No description')[:500]}

TAGS: {', '.join(video_data.get('tags', [])[:10])}

TRANSCRIPT EXCERPT: {video_data.get('transcript', 'No transcript')[:2000]}

Generate a viral thumbnail concept for this video.
"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.8
        )

        return json.loads(response.choices[0].message.content)
```

### 3.7 Create Reference Analyzer Service

Create `backend/services/reference_analyzer.py`:

```python
import openai
import json
import base64
from typing import List, Optional

class ReferenceAnalyzer:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def analyze_reference_thumbnails(self, images: List[dict]) -> dict:
        """Analyze reference thumbnails to extract style characteristics."""

        messages = [
            {
                "role": "system",
                "content": """Analyze these YouTube thumbnails and extract their visual style characteristics.

Return a JSON object with:
{
    "composition": {"layout": "...", "subject_position": "...", "background_style": "..."},
    "colors": {"dominant": ["..."], "accent": ["..."], "mood": "..."},
    "lighting": {"type": "...", "direction": "...", "intensity": "..."},
    "text_style": {"position": "...", "size": "...", "style": "..."},
    "mood": "...",
    "style_summary": "A brief description of the overall style to replicate"
}"""
            }
        ]

        content = [{"type": "text", "text": "Analyze these reference thumbnails:"}]

        for img in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img['data']}"}
            })
            if img.get('description'):
                content.append({"type": "text", "text": f"Description: {img['description']}"})

        messages.append({"role": "user", "content": content})

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=1000
        )

        return json.loads(response.choices[0].message.content)

    def analyze_face_photos(self, images: List[str]) -> dict:
        """
        Analyze ALL face photos individually. Returns structured data for each person.

        IMPORTANT: First photo = PRIMARY person (main character/reactor)
                   Additional photos = SECONDARY people (replace other faces in reference)

        Returns dict with:
        - faces: list of {index, role, description}
        - primary_face: description of first person
        - secondary_faces: list of descriptions for other people
        - combined_description: summary of all people
        """
        if not images:
            return {"faces": [], "primary_face": "", "secondary_faces": [], "combined_description": ""}

        content = [
            {"type": "text", "text": f"Analyze these {len(images)} face photos. Each is a DIFFERENT person:"}
        ]

        for i, img_data in enumerate(images):
            role = "PRIMARY - main character/reactor" if i == 0 else "SECONDARY - supporting character"
            content.append({"type": "text", "text": f"\n--- PERSON {i + 1} ({role}) ---"})
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}
            })

        system_prompt = """Analyze each face photo and return JSON:
{
    "faces": [
        {"index": 1, "role": "primary", "description": "Detailed description of person 1"},
        {"index": 2, "role": "secondary", "description": "Detailed description of person 2"}
    ],
    "combined_description": "Summary of all people"
}
Be detailed: ethnicity, skin tone, hair, facial features, age, gender."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )

        result = json.loads(response.choices[0].message.content)

        # Extract primary and secondary for easy access
        faces = result.get("faces", [])
        result["primary_face"] = faces[0]["description"] if faces else ""
        result["secondary_faces"] = [f["description"] for f in faces[1:]] if len(faces) > 1 else []

        return result

    def generate_style_enhanced_prompt(
        self,
        base_prompt: str,
        reference_analysis: Optional[dict] = None,
        face_description: Optional[dict] = None,  # Now expects dict, not string
    ) -> str:
        """Enhance a prompt with reference style and ALL face descriptions."""

        enhanced = base_prompt

        if reference_analysis:
            style = reference_analysis.get('style_summary', '')
            if style:
                enhanced += f". Style: {style}"

        # Handle face_description - can be dict (new) or string (legacy)
        if face_description:
            if isinstance(face_description, dict):
                primary = face_description.get("primary_face", "")
                secondary = face_description.get("secondary_faces", [])

                if primary:
                    enhanced += f"\n\nPRIMARY PERSON (main character): {primary}"
                for i, sec in enumerate(secondary):
                    enhanced += f"\n\nSECONDARY PERSON {i+1}: {sec}"
            else:
                # Legacy string format
                enhanced = enhanced.replace("a person", f"a person ({face_description})")

        return enhanced
```

### 3.8 Create Image Generator Service (Google Gemini)

Create `backend/services/imagen_generator.py`:

```python
from google import genai
from google.genai import types
import base64
import time
from typing import Optional, List

class ImagenGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def generate_thumbnail(
        self,
        prompt: str,
        num_images: int = 4,
        reference_image: Optional[str] = None,
        face_image: Optional[str] = None,
    ) -> dict:
        start_time = time.time()

        # Enhance prompt for thumbnail style
        enhanced_prompt = f"""YouTube thumbnail, 16:9 aspect ratio, high quality, vibrant colors, professional lighting, {prompt}"""

        # Build the request
        contents = []

        # Add reference image if provided
        if reference_image:
            contents.append(types.Part.from_bytes(
                data=base64.b64decode(reference_image),
                mime_type="image/jpeg"
            ))
            contents.append("Match the style of this reference image. ")

        # Add face image if provided
        if face_image:
            contents.append(types.Part.from_bytes(
                data=base64.b64decode(face_image),
                mime_type="image/jpeg"
            ))
            contents.append("Include this person's face in the thumbnail. ")

        contents.append(enhanced_prompt)

        # Generate images
        response = await self.client.aio.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=enhanced_prompt if not contents[:-1] else None,
            config=types.GenerateImagesConfig(
                number_of_images=min(num_images, 4),
                aspect_ratio="16:9",
                safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            )
        )

        # Convert to base64 data URLs
        images = []
        for img in response.generated_images:
            b64 = base64.b64encode(img.image.image_bytes).decode('utf-8')
            images.append(f"data:image/png;base64,{b64}")

        generation_time = int((time.time() - start_time) * 1000)

        return {
            "images": images,
            "generation_time_ms": generation_time
        }
```

### 3.9 Create Text Overlay Service

Create `backend/services/text_overlay.py`:

```python
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import Tuple, Optional

class TextOverlayService:
    def __init__(self):
        self.fonts = {
            'impact': self._get_font('Impact', 80),
            'arial_bold': self._get_font('Arial Bold', 72),
            'default': self._get_font(None, 72),
        }

    def _get_font(self, name: Optional[str], size: int) -> ImageFont.FreeTypeFont:
        try:
            if name:
                return ImageFont.truetype(name, size)
        except:
            pass
        return ImageFont.load_default()

    def _decode_image(self, image_data: str) -> Image.Image:
        if image_data.startswith('data:'):
            image_data = image_data.split(',')[1]
        return Image.open(io.BytesIO(base64.b64decode(image_data))).convert('RGBA')

    def _encode_image(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.convert('RGB').save(buffer, format='PNG')
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    def add_gradient_background(
        self,
        image_data: str,
        position: str = "bottom",
        opacity: float = 0.5,
        height_ratio: float = 0.35,
    ) -> str:
        img = self._decode_image(image_data)
        width, height = img.size

        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)

        gradient_height = int(height * height_ratio)

        if position == "bottom":
            for y in range(gradient_height):
                alpha = int(255 * opacity * (y / gradient_height))
                draw.line([(0, height - gradient_height + y), (width, height - gradient_height + y)],
                         fill=(0, 0, 0, alpha))

        img = Image.alpha_composite(img, gradient)
        return self._encode_image(img)

    def add_text(
        self,
        image_data: str,
        text: str,
        position: str = "bottom_center",
        font_preset: str = "impact",
        color_preset: str = "white_shadow",
        font_size: Optional[int] = None,
        stroke_width: int = 3,
        shadow_offset: int = 3,
    ) -> str:
        img = self._decode_image(image_data)
        draw = ImageDraw.Draw(img)

        width, height = img.size

        # Get font
        font = self.fonts.get(font_preset, self.fonts['default'])
        if font_size:
            try:
                font = ImageFont.truetype(font.path, font_size)
            except:
                pass

        # Calculate text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position
        if position == "bottom_center":
            x = (width - text_width) // 2
            y = height - text_height - 40
        elif position == "center":
            x = (width - text_width) // 2
            y = (height - text_height) // 2
        elif position == "top_center":
            x = (width - text_width) // 2
            y = 40
        else:
            x = (width - text_width) // 2
            y = height - text_height - 40

        # Draw shadow
        if color_preset == "white_shadow":
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 200))
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255),
                     stroke_width=stroke_width, stroke_fill=(0, 0, 0, 255))
        elif color_preset == "yellow_shadow":
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 200))
            draw.text((x, y), text, font=font, fill=(255, 255, 0, 255),
                     stroke_width=stroke_width, stroke_fill=(0, 0, 0, 255))

        return self._encode_image(img)
```

### 3.10 Create Services Init

Create `backend/services/__init__.py`:

```python
from .video_analyzer import VideoAnalyzer
from .prompt_generator import PromptGenerator
from .imagen_generator import ImagenGenerator
from .reference_analyzer import ReferenceAnalyzer
from .text_overlay import TextOverlayService

__all__ = [
    'VideoAnalyzer',
    'PromptGenerator',
    'ImagenGenerator',
    'ReferenceAnalyzer',
    'TextOverlayService',
]
```

### 3.11 Create Main FastAPI Application

Create `backend/main.py`:

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional

from config import settings
from models import (
    VideoURLRequest,
    PromptRequest,
    ThumbnailResponse,
    TemplateResponse,
    HealthResponse,
)
from services import (
    VideoAnalyzer,
    PromptGenerator,
    ImagenGenerator,
    ReferenceAnalyzer,
    TextOverlayService,
)

# Templates
TEMPLATES = {
    "mrbeast": {
        "id": "mrbeast",
        "name": "Viral/MrBeast Style",
        "category": "entertainment",
        "description": "High-energy thumbnails with extreme expressions",
    },
    "educational": {
        "id": "educational",
        "name": "Educational/Explainer",
        "category": "education",
        "description": "Professional, authoritative thumbnails",
    },
    "tech": {
        "id": "tech",
        "name": "Tech/Product Review",
        "category": "technology",
        "description": "Sleek, modern tech thumbnails",
    },
    "minimalist": {
        "id": "minimalist",
        "name": "Clean/Minimalist",
        "category": "lifestyle",
        "description": "Clean, aesthetic thumbnails",
    },
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize services
    app.state.video_analyzer = VideoAnalyzer(settings.youtube_api_key)
    app.state.prompt_generator = PromptGenerator(settings.openai_api_key)
    app.state.reference_analyzer = ReferenceAnalyzer(settings.openai_api_key)
    app.state.text_overlay = TextOverlayService()

    if settings.google_ai_api_key:
        app.state.imagen_generator = ImagenGenerator(settings.google_ai_api_key)
    else:
        app.state.imagen_generator = None

    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency getters
def get_video_analyzer() -> VideoAnalyzer:
    return app.state.video_analyzer

def get_prompt_generator() -> PromptGenerator:
    return app.state.prompt_generator

def get_reference_analyzer() -> ReferenceAnalyzer:
    return app.state.reference_analyzer

def get_imagen_generator() -> Optional[ImagenGenerator]:
    return getattr(app.state, 'imagen_generator', None)

def get_text_overlay() -> TextOverlayService:
    return app.state.text_overlay

# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", version=settings.api_version)

@app.get("/templates", response_model=list[TemplateResponse])
async def get_templates():
    return [TemplateResponse(**t) for t in TEMPLATES.values()]

@app.post("/generate/from-url", response_model=ThumbnailResponse)
async def generate_from_url(
    request: VideoURLRequest,
    video_analyzer: VideoAnalyzer = Depends(get_video_analyzer),
    prompt_generator: PromptGenerator = Depends(get_prompt_generator),
    reference_analyzer: ReferenceAnalyzer = Depends(get_reference_analyzer),
    imagen_generator: Optional[ImagenGenerator] = Depends(get_imagen_generator),
    text_overlay: TextOverlayService = Depends(get_text_overlay),
):
    try:
        # 1. Analyze video
        video_data = video_analyzer.analyze(request.url)

        # 2. Analyze reference thumbnails if provided
        reference_analysis = None
        if request.reference_thumbnails:
            reference_data = [{"data": ref.data, "description": ref.description}
                           for ref in request.reference_thumbnails]
            reference_analysis = reference_analyzer.analyze_reference_thumbnails(reference_data)

        # 3. Analyze face photos if provided
        face_description = None
        if request.face_images:
            face_description = reference_analyzer.analyze_face_photos(request.face_images)

        # 4. Generate prompt
        prompt_data = prompt_generator.generate_prompt(
            video_data,
            reference_analysis=reference_analysis,
            face_description=face_description,
        )

        # 5. Generate images
        if imagen_generator is None:
            raise HTTPException(status_code=500, detail="Image generator not configured")

        reference_image = request.reference_thumbnails[0].data if request.reference_thumbnails else None
        face_image = request.face_images[0] if request.face_images else None

        result = await imagen_generator.generate_thumbnail(
            prompt=prompt_data["prompt"],
            num_images=request.num_variations,
            reference_image=reference_image,
            face_image=face_image,
        )

        # 6. Add text overlay if enabled
        thumbnail_text = prompt_data.get("thumbnail_text", "")
        final_images = result["images"]

        if thumbnail_text and request.add_text_overlay:
            final_images = []
            for img in result["images"]:
                img_with_gradient = text_overlay.add_gradient_background(img)
                img_with_text = text_overlay.add_text(
                    image_data=img_with_gradient,
                    text=thumbnail_text.upper(),
                    position="bottom_center",
                    font_preset="impact",
                    color_preset="white_shadow",
                )
                final_images.append(img_with_text)

        return ThumbnailResponse(
            images=final_images,
            prompt_used=prompt_data["prompt"],
            thumbnail_text=thumbnail_text,
            generation_time_ms=result.get("generation_time_ms"),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/generate/from-prompt", response_model=ThumbnailResponse)
async def generate_from_prompt(
    request: PromptRequest,
    reference_analyzer: ReferenceAnalyzer = Depends(get_reference_analyzer),
    imagen_generator: Optional[ImagenGenerator] = Depends(get_imagen_generator),
):
    try:
        if imagen_generator is None:
            raise HTTPException(status_code=500, detail="Image generator not configured")

        # Enhance prompt with references if provided
        enhanced_prompt = request.prompt

        if request.reference_thumbnails:
            reference_data = [{"data": ref.data, "description": ref.description}
                           for ref in request.reference_thumbnails]
            analysis = reference_analyzer.analyze_reference_thumbnails(reference_data)
            enhanced_prompt = reference_analyzer.generate_style_enhanced_prompt(
                request.prompt, analysis
            )

        result = await imagen_generator.generate_thumbnail(
            prompt=enhanced_prompt,
            num_images=request.num_variations,
        )

        return ThumbnailResponse(
            images=result["images"],
            prompt_used=enhanced_prompt,
            generation_time_ms=result.get("generation_time_ms"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.debug)
```

### 3.12 Create Environment File

Create `backend/.env`:

```env
DEBUG=true

# AI Services (REQUIRED)
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_AI_API_KEY=your-google-ai-key

# YouTube (REQUIRED)
YOUTUBE_API_KEY=your-youtube-api-key

# Optional
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
```

---

## STEP 4: Get API Keys

1. **Google AI API Key** (for Gemini/Imagen)
   - Go to https://aistudio.google.com/apikey
   - Create a new API key

2. **OpenAI API Key** (for GPT-4o prompt generation)
   - Go to https://platform.openai.com/api-keys
   - Create a new secret key

3. **YouTube Data API Key**
   - Go to https://console.cloud.google.com
   - Create a new project
   - Enable "YouTube Data API v3"
   - Create credentials (API key)

---

## STEP 5: Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Open:** http://localhost:3000

---

## Summary of What Was Built

1. **Frontend (Next.js)**
   - Mode toggle between URL and Prompt input
   - YouTube URL input with validation
   - Custom prompt textarea
   - Style template selector
   - Reference image uploader (drag & drop)
   - Face photo uploader (drag & drop)
   - Text overlay toggle
   - Generate button with loading state
   - Results gallery with 4 thumbnail variations
   - Download functionality

2. **Backend (FastAPI)**
   - Video analysis (YouTube API + transcript)
   - Reference image analysis (GPT-4o vision)
   - Face photo analysis (GPT-4o vision)
   - Prompt generation (GPT-4o)
   - Image generation (Google Imagen)
   - Text overlay (Pillow)

3. **AI Pipeline Flow:**
   ```
   YouTube URL → Extract metadata + transcript
        ↓
   Reference images → Analyze style with GPT-4o
        ↓
   Face photos → Describe appearance with GPT-4o
        ↓
   Generate prompt → GPT-4o creates optimized prompt
        ↓
   Generate images → Google Imagen creates 4 variations
        ↓
   Add text overlay → Pillow adds text with gradient
        ↓
   Return results → Display in frontend gallery
   ```
