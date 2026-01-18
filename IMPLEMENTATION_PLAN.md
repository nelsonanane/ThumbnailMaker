# AI Thumbnail Generator - Implementation Plan

## Executive Summary

This plan synthesizes the best features from **ThumbnailCreator.com** (deep video analysis, LoRA training, natural language editing) and **ThumbMagic.co** (speed, templates, simplicity) into a unified implementation approach.

---

## 1. Core Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  URL Input   │  │   Template   │  │   Canvas     │  │   Gallery    │     │
│  │  Component   │  │   Selector   │  │   Editor     │  │   View       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ REST API / WebSocket
┌────────────────────────────────────▼────────────────────────────────────────┐
│                           BACKEND (Python/FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Video      │  │   Prompt     │  │   Job        │  │   User       │     │
│  │   Analyzer   │  │   Generator  │  │   Queue      │  │   Manager    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                            AI INFERENCE LAYER                                │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐     │
│  │  fal.ai / Replicate│  │   OpenAI / Claude  │  │  YouTube Data API  │     │
│  │  (Flux, LoRA)      │  │   (Prompt Engine)  │  │  (Transcripts)     │     │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Feature Matrix: Best of Both Platforms

| Feature | Source | Priority | Implementation Complexity |
|---------|--------|----------|---------------------------|
| Video URL to Thumbnail | ThumbnailCreator | HIGH | Medium |
| Template/Style Library | ThumbMagic | HIGH | Low |
| LoRA Face Training | ThumbnailCreator | HIGH | Medium |
| Single-Shot Avatar (InstantID) | ThumbMagic | HIGH | Low |
| Natural Language Editing | ThumbnailCreator | MEDIUM | Medium |
| 3-Click Quick Mode | ThumbMagic | MEDIUM | Low |
| Text Inpainting | ThumbnailCreator | MEDIUM | Medium |
| A/B Testing Integration | ThumbnailCreator | LOW | High |

---

## 3. Technology Stack

### 3.1 Frontend

| Component | Technology | Justification |
|-----------|------------|---------------|
| Framework | **Next.js 14+** (App Router) | SSR, API routes, React Server Components |
| Styling | **Tailwind CSS** | Rapid UI development, consistent design |
| State Management | **Zustand** | Lightweight, TypeScript-friendly |
| Canvas Editor | **Fabric.js** | Rich canvas manipulation for manual edits |
| Real-time Updates | **WebSocket** or **SSE** | Job status updates |
| File Upload | **react-dropzone** | Drag-and-drop image uploads |

### 3.2 Backend

| Component | Technology | Justification |
|-----------|------------|---------------|
| Server Framework | **FastAPI** (Python) | Async-first, auto OpenAPI docs, ML ecosystem |
| Database | **PostgreSQL** via **Supabase** | Managed, real-time subscriptions, auth |
| Job Queue | **Redis** + **Celery** or **BullMQ** | Async job processing |
| Asset Storage | **AWS S3** or **Cloudflare R2** | Cost-effective object storage |
| Authentication | **Supabase Auth** or **Clerk** | OAuth, social login, user management |

### 3.3 AI Services

| Service | Provider | Cost | Purpose |
|---------|----------|------|---------|
| Image Generation | **fal.ai** (FLUX.2 Turbo) | $0.008/image | Primary generation |
| LoRA Training | **fal.ai** (flux-lora-portrait-trainer) | ~$2/training | Face model training |
| Single-Shot Face | **fal.ai** or **Replicate** (InstantID) | ~$0.03/image | Quick avatar mode |
| Inpainting | **fal.ai** (flux-pro/v1/fill) | $0.05/MP | Text/element editing |
| Prompt Generation | **OpenAI GPT-4o** or **Claude 3.5 Sonnet** | ~$0.01/call | Video analysis & prompts |
| Transcripts | **youtube-transcript-api** (Python) | FREE | No API key needed |
| Video Metadata | **YouTube Data API v3** | FREE (10k quota/day) | Title, tags, description |

---

## 4. Implementation Phases

### Phase 1: Foundation (Week 1-2)

#### 4.1.1 Project Setup

```bash
# Frontend
npx create-next-app@latest thumbnail-maker --typescript --tailwind --app
cd thumbnail-maker
npm install zustand @fal-ai/client fabric react-dropzone

# Backend
mkdir backend && cd backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn fal-client openai youtube-transcript-api \
    google-api-python-client python-multipart celery redis supabase
```

#### 4.1.2 Database Schema (Supabase/PostgreSQL)

```sql
-- Users table (managed by Supabase Auth)
-- Additional user data
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    credits INTEGER DEFAULT 10,
    subscription_tier TEXT DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Face Models (LoRA)
CREATE TABLE face_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    name TEXT NOT NULL,
    trigger_word TEXT NOT NULL,
    lora_url TEXT NOT NULL,
    training_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Generated Thumbnails
CREATE TABLE thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    video_url TEXT,
    prompt TEXT,
    template_id TEXT,
    image_url TEXT NOT NULL,
    face_model_id UUID REFERENCES face_models(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Templates
CREATE TABLE templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    example_image_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4.1.3 Environment Variables

```env
# .env.local (Frontend)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# .env (Backend)
FAL_KEY=your-fal-api-key
OPENAI_API_KEY=your-openai-key
YOUTUBE_API_KEY=your-youtube-api-key
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_KEY=your-service-key
REDIS_URL=redis://localhost:6379
```

---

### Phase 2: Core Video-to-Thumbnail Pipeline (Week 2-3)

#### 4.2.1 Video Analysis Service

```python
# backend/services/video_analyzer.py
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import re

class VideoAnalyzer:
    def __init__(self, youtube_api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        self.transcript_api = YouTubeTranscriptApi()

    def extract_video_id(self, url: str) -> str:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError("Invalid YouTube URL")

    def get_metadata(self, video_id: str) -> dict:
        """Fetch video metadata from YouTube Data API."""
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
        """Fetch video transcript."""
        try:
            transcript_list = self.transcript_api.list(video_id)
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            fetched = transcript.fetch()

            # Combine text segments
            full_text = ' '.join([entry['text'] for entry in fetched.to_raw_data()])
            return full_text[:5000]  # Limit for LLM context
        except Exception as e:
            return ""  # Return empty if no transcript available

    def analyze(self, url: str) -> dict:
        """Complete video analysis."""
        video_id = self.extract_video_id(url)
        metadata = self.get_metadata(video_id)
        transcript = self.get_transcript(video_id)

        return {
            'video_id': video_id,
            **metadata,
            'transcript': transcript,
        }
```

#### 4.2.2 Prompt Generator Service

```python
# backend/services/prompt_generator.py
import openai
from typing import Optional

SYSTEM_PROMPT = """You are a YouTube Thumbnail Architect specializing in viral, high-CTR thumbnail designs.

Your task: Analyze the video content and generate a detailed image prompt for FLUX AI.

RULES:
1. SUBJECT: If a person is mentioned, use the token "{trigger_word}" to represent them. Describe their expression (shocked, excited, skeptical, pointing).
2. COMPOSITION: Use proven layouts - split screen, close-up face on right, object on left, or centered dramatic pose.
3. TEXT: Include SHORT punchy text (2-4 words max) that creates curiosity. Put text in quotes.
4. LIGHTING: Always specify dramatic lighting - rim light, volumetric, god rays, studio softbox.
5. STYLE: Include quality tokens - 4k, hyper-realistic, sharp focus, vibrant colors.
6. BACKGROUND: Describe a relevant, slightly blurred background that adds context.

OUTPUT FORMAT:
Return ONLY a JSON object with these fields:
{
    "prompt": "The complete FLUX image generation prompt",
    "thumbnail_text": "The 2-4 word text overlay",
    "emotion": "The primary emotion to convey",
    "composition": "Brief description of the layout"
}
"""

class PromptGenerator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def generate_prompt(
        self,
        video_data: dict,
        template_id: Optional[str] = None,
        trigger_word: str = "person"
    ) -> dict:
        """Generate a thumbnail prompt from video analysis."""

        user_content = f"""
VIDEO TITLE: {video_data.get('title', 'Unknown')}

VIDEO DESCRIPTION: {video_data.get('description', 'No description')[:500]}

TAGS: {', '.join(video_data.get('tags', [])[:10])}

TRANSCRIPT EXCERPT: {video_data.get('transcript', 'No transcript')[:2000]}

TRIGGER WORD FOR PERSON: {trigger_word}

Generate a viral thumbnail concept for this video.
"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.8
        )

        import json
        return json.loads(response.choices[0].message.content)
```

#### 4.2.3 Image Generation Service

```python
# backend/services/image_generator.py
import fal_client
from typing import Optional, List

class ImageGenerator:
    def __init__(self):
        # fal_client uses FAL_KEY env var automatically
        pass

    async def generate_thumbnail(
        self,
        prompt: str,
        lora_url: Optional[str] = None,
        lora_scale: float = 1.0,
        num_images: int = 4
    ) -> List[str]:
        """Generate thumbnail images using FLUX."""

        arguments = {
            "prompt": prompt,
            "image_size": "landscape_16_9",  # YouTube thumbnail ratio
            "num_inference_steps": 28,
            "guidance_scale": 3.5,  # Optimal for FLUX
            "num_images": num_images,
        }

        # Add LoRA if provided (trained face model)
        if lora_url:
            arguments["loras"] = [{"path": lora_url, "scale": lora_scale}]

        # Use FLUX.2 Turbo for speed, or flux-lora for LoRA support
        endpoint = "fal-ai/flux-lora" if lora_url else "fal-ai/flux/dev"

        result = await fal_client.run_async(endpoint, arguments=arguments)

        return [img["url"] for img in result["images"]]

    async def generate_with_face(
        self,
        prompt: str,
        face_image_url: str,
    ) -> List[str]:
        """Generate with single-shot face consistency (InstantID-style)."""

        # Use Flux Kontext for face reference
        result = await fal_client.run_async(
            "fal-ai/flux-kontext",
            arguments={
                "prompt": prompt,
                "image_url": face_image_url,
                "image_size": "landscape_16_9",
                "num_inference_steps": 28,
            }
        )

        return [img["url"] for img in result["images"]]

    async def inpaint(
        self,
        image_url: str,
        mask_url: str,
        prompt: str,
    ) -> str:
        """Inpaint a region of an image (for text editing)."""

        result = await fal_client.run_async(
            "fal-ai/flux-pro/v1/fill",
            arguments={
                "image_url": image_url,
                "mask_url": mask_url,
                "prompt": prompt,
            }
        )

        return result["images"][0]["url"]
```

---

### Phase 3: Face Model Training (Week 3-4)

#### 4.3.1 LoRA Training Service

```python
# backend/services/lora_trainer.py
import fal_client
from supabase import create_client
import os

class LoRATrainer:
    def __init__(self):
        self.supabase = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"]
        )

    async def start_training(
        self,
        user_id: str,
        images_zip_url: str,
        model_name: str,
    ) -> dict:
        """Start LoRA training for face model."""

        trigger_word = f"FACE_{user_id[:8].upper()}"

        # Create database record
        record = self.supabase.table("face_models").insert({
            "user_id": user_id,
            "name": model_name,
            "trigger_word": trigger_word,
            "lora_url": "",
            "training_status": "training"
        }).execute()

        model_id = record.data[0]["id"]

        # Start fal.ai training
        def on_update(update):
            if hasattr(update, 'logs'):
                for log in update.logs:
                    print(f"Training: {log['message']}")

        result = await fal_client.subscribe_async(
            "fal-ai/flux-lora-portrait-trainer",
            arguments={
                "images_data_url": images_zip_url,
                "trigger_word": trigger_word,
                "steps": 1000,
                "is_style": False,
                "face_crop_enabled": True,
                "create_masks": True,
            },
            with_logs=True,
            on_queue_update=on_update,
        )

        # Update database with trained LoRA URL
        lora_url = result["diffusers_lora_file"]["url"]

        self.supabase.table("face_models").update({
            "lora_url": lora_url,
            "training_status": "completed"
        }).eq("id", model_id).execute()

        return {
            "model_id": model_id,
            "trigger_word": trigger_word,
            "lora_url": lora_url,
        }
```

---

### Phase 4: Template System (Week 4)

#### 4.4.1 Template Definitions

```python
# backend/templates/definitions.py

TEMPLATES = {
    "mrbeast": {
        "name": "Viral/MrBeast Style",
        "category": "entertainment",
        "system_prompt": """
Create a high-energy, viral-style thumbnail with:
- EXTREME facial expression (shocked, ecstatic, or terrified)
- Bold, saturated colors (yellow, red, blue dominance)
- Large contrasting text with drop shadow
- Split composition: face on one side, dramatic object/scene on other
- Lighting: Strong rim light, high contrast, studio quality
- Style: Hyper-real, 4K, Unreal Engine aesthetic
        """,
        "example_prompt": "A {trigger_word} man with shocked expression, mouth wide open, eyes bulging, standing next to a massive pile of gold bars, split composition, vibrant yellow and blue lighting, text 'IMPOSSIBLE' in bold white with black outline, 4k hyper-realistic, studio lighting"
    },
    "educational": {
        "name": "Educational/Explainer",
        "category": "education",
        "system_prompt": """
Create a professional, authoritative thumbnail with:
- Confident, approachable expression (slight smile, direct eye contact)
- Clean, minimalist background (gradient or soft blur)
- Clear, readable text in professional font
- Visual aid element (chart, icon, or diagram)
- Lighting: Soft, professional, even illumination
- Style: Sharp, professional, trustworthy
        """,
        "example_prompt": "A {trigger_word} person in professional attire, confident smile, pointing at a floating holographic chart with upward arrow, clean blue gradient background, text 'SECRETS REVEALED' in bold yellow sans-serif, soft professional lighting, 8k sharp focus"
    },
    "tech": {
        "name": "Tech/Product Review",
        "category": "technology",
        "system_prompt": """
Create a sleek, modern tech thumbnail with:
- Product prominently displayed with dramatic lighting
- Person showing curiosity or excitement about the product
- Dark/moody background with accent lighting
- Minimal but impactful text
- Lighting: Product spotlight, rim lighting on person
- Style: Premium, cinematic, Apple-aesthetic
        """,
        "example_prompt": "A {trigger_word} person holding a glowing smartphone, looking amazed, dark moody background with blue and purple accent lights, product spotlight, text 'GAME CHANGER' in sleek white font, cinematic lighting, 4k"
    },
    "controversy": {
        "name": "Drama/Controversy",
        "category": "entertainment",
        "system_prompt": """
Create a tension-filled, dramatic thumbnail with:
- Serious or concerned facial expression
- Red/orange warning color accents
- Split or versus composition if applicable
- Urgent, impactful text
- Lighting: Dramatic, high contrast, moody
- Style: News-style urgency, high stakes feel
        """,
        "example_prompt": "A {trigger_word} person with serious concerned expression, furrowed brows, red warning glow on one side, dark dramatic background, text 'THE TRUTH' in bold red letters, high contrast dramatic lighting, 4k cinematic"
    },
    "minimalist": {
        "name": "Clean/Minimalist",
        "category": "lifestyle",
        "system_prompt": """
Create a clean, aesthetic thumbnail with:
- Calm, composed expression
- Lots of negative space
- Soft, muted color palette
- Elegant, thin typography
- Lighting: Natural, soft, airy
- Style: Instagram aesthetic, lifestyle brand feel
        """,
        "example_prompt": "A {trigger_word} person in casual elegant clothing, soft smile, white/beige minimalist background with soft shadows, small elegant text 'simple living' in thin serif font, natural window lighting, clean aesthetic, 4k"
    }
}
```

---

### Phase 5: API Endpoints (Week 4-5)

#### 4.5.1 FastAPI Application

```python
# backend/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os

from services.video_analyzer import VideoAnalyzer
from services.prompt_generator import PromptGenerator
from services.image_generator import ImageGenerator
from services.lora_trainer import LoRATrainer
from templates.definitions import TEMPLATES

app = FastAPI(title="Thumbnail Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
video_analyzer = VideoAnalyzer(os.environ["YOUTUBE_API_KEY"])
prompt_generator = PromptGenerator(os.environ["OPENAI_API_KEY"])
image_generator = ImageGenerator()
lora_trainer = LoRATrainer()

# Request/Response Models
class VideoURLRequest(BaseModel):
    url: str
    template_id: Optional[str] = None
    face_model_id: Optional[str] = None
    num_variations: int = 4

class PromptRequest(BaseModel):
    prompt: str
    template_id: Optional[str] = None
    face_model_id: Optional[str] = None
    face_image_url: Optional[str] = None  # For single-shot mode
    num_variations: int = 4

class ThumbnailResponse(BaseModel):
    images: List[str]
    prompt_used: str
    thumbnail_text: str

class TrainingRequest(BaseModel):
    model_name: str
    images_zip_url: str

# Endpoints
@app.get("/templates")
async def get_templates():
    """Get all available thumbnail templates."""
    return {
        "templates": [
            {"id": k, "name": v["name"], "category": v["category"]}
            for k, v in TEMPLATES.items()
        ]
    }

@app.post("/generate/from-url", response_model=ThumbnailResponse)
async def generate_from_url(request: VideoURLRequest):
    """Generate thumbnails from a YouTube URL."""
    try:
        # Step 1: Analyze video
        video_data = video_analyzer.analyze(request.url)

        # Step 2: Get face model if specified
        lora_url = None
        trigger_word = "person"
        if request.face_model_id:
            # Fetch from database
            # lora_url = ...
            # trigger_word = ...
            pass

        # Step 3: Generate prompt
        prompt_data = prompt_generator.generate_prompt(
            video_data,
            template_id=request.template_id,
            trigger_word=trigger_word
        )

        # Step 4: Generate images
        images = await image_generator.generate_thumbnail(
            prompt=prompt_data["prompt"],
            lora_url=lora_url,
            num_images=request.num_variations
        )

        return ThumbnailResponse(
            images=images,
            prompt_used=prompt_data["prompt"],
            thumbnail_text=prompt_data["thumbnail_text"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/from-prompt", response_model=ThumbnailResponse)
async def generate_from_prompt(request: PromptRequest):
    """Generate thumbnails from a custom prompt."""
    try:
        if request.face_image_url:
            # Single-shot mode with InstantID-style
            images = await image_generator.generate_with_face(
                prompt=request.prompt,
                face_image_url=request.face_image_url
            )
        else:
            images = await image_generator.generate_thumbnail(
                prompt=request.prompt,
                num_images=request.num_variations
            )

        return ThumbnailResponse(
            images=images,
            prompt_used=request.prompt,
            thumbnail_text=""
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/face-models/train")
async def train_face_model(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    user_id: str = "demo-user"  # Would come from auth
):
    """Start LoRA training for a face model."""
    # Add to background task queue
    background_tasks.add_task(
        lora_trainer.start_training,
        user_id,
        request.images_zip_url,
        request.model_name
    )

    return {"status": "training_started", "message": "Check back in ~20 minutes"}

@app.get("/face-models")
async def list_face_models(user_id: str = "demo-user"):
    """List user's trained face models."""
    # Fetch from database
    return {"models": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### Phase 6: Frontend Implementation (Week 5-6)

#### 4.6.1 Key Components Structure

```
src/
├── app/
│   ├── page.tsx              # Landing/Generator page
│   ├── templates/page.tsx    # Template browser
│   ├── face-models/page.tsx  # Face model management
│   └── api/                   # API routes (if needed)
├── components/
│   ├── URLInput.tsx          # YouTube URL input
│   ├── TemplateSelector.tsx  # Template grid
│   ├── ThumbnailCanvas.tsx   # Fabric.js editor
│   ├── ImageGallery.tsx      # Generated images grid
│   ├── FaceUploader.tsx      # Face photo uploader
│   └── PromptEditor.tsx      # Manual prompt editing
├── stores/
│   └── thumbnailStore.ts     # Zustand state
├── services/
│   └── api.ts                # API client
└── lib/
    └── utils.ts
```

#### 4.6.2 Main State Store

```typescript
// src/stores/thumbnailStore.ts
import { create } from 'zustand';

interface ThumbnailState {
  // Input state
  videoUrl: string;
  customPrompt: string;
  selectedTemplate: string | null;
  selectedFaceModel: string | null;
  faceImageUrl: string | null;

  // Generation state
  isGenerating: boolean;
  generatedImages: string[];
  promptUsed: string;
  thumbnailText: string;

  // Face models
  faceModels: FaceModel[];
  isTraining: boolean;

  // Actions
  setVideoUrl: (url: string) => void;
  setCustomPrompt: (prompt: string) => void;
  setSelectedTemplate: (id: string | null) => void;
  setSelectedFaceModel: (id: string | null) => void;
  setFaceImageUrl: (url: string | null) => void;
  generateFromUrl: () => Promise<void>;
  generateFromPrompt: () => Promise<void>;
  trainFaceModel: (images: File[], name: string) => Promise<void>;
}

export const useThumbnailStore = create<ThumbnailState>((set, get) => ({
  videoUrl: '',
  customPrompt: '',
  selectedTemplate: null,
  selectedFaceModel: null,
  faceImageUrl: null,
  isGenerating: false,
  generatedImages: [],
  promptUsed: '',
  thumbnailText: '',
  faceModels: [],
  isTraining: false,

  setVideoUrl: (url) => set({ videoUrl: url }),
  setCustomPrompt: (prompt) => set({ customPrompt: prompt }),
  setSelectedTemplate: (id) => set({ selectedTemplate: id }),
  setSelectedFaceModel: (id) => set({ selectedFaceModel: id }),
  setFaceImageUrl: (url) => set({ faceImageUrl: url }),

  generateFromUrl: async () => {
    const { videoUrl, selectedTemplate, selectedFaceModel } = get();
    set({ isGenerating: true });

    try {
      const response = await fetch('/api/generate/from-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: videoUrl,
          template_id: selectedTemplate,
          face_model_id: selectedFaceModel,
        }),
      });

      const data = await response.json();
      set({
        generatedImages: data.images,
        promptUsed: data.prompt_used,
        thumbnailText: data.thumbnail_text,
      });
    } finally {
      set({ isGenerating: false });
    }
  },

  generateFromPrompt: async () => {
    const { customPrompt, faceImageUrl } = get();
    set({ isGenerating: true });

    try {
      const response = await fetch('/api/generate/from-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: customPrompt,
          face_image_url: faceImageUrl,
        }),
      });

      const data = await response.json();
      set({
        generatedImages: data.images,
        promptUsed: data.prompt_used,
      });
    } finally {
      set({ isGenerating: false });
    }
  },

  trainFaceModel: async (images, name) => {
    set({ isTraining: true });
    // Upload images, start training...
    set({ isTraining: false });
  },
}));
```

---

## 5. Cost Estimation

### Per-Thumbnail Costs (Using fal.ai)

| Component | Cost |
|-----------|------|
| FLUX.2 Turbo (4 variations) | $0.032 |
| GPT-4o prompt generation | ~$0.01 |
| YouTube API | FREE |
| **Total per generation** | **~$0.042** |

### Face Model Training

| Item | Cost |
|------|------|
| LoRA training (1000 steps) | ~$2.00 |
| Amortized over 100 thumbnails | $0.02/thumbnail |

### Monthly Operating Costs (1000 users, 10 generations each)

| Item | Cost |
|------|------|
| 10,000 thumbnail generations | $420 |
| 100 LoRA trainings | $200 |
| Supabase (Pro) | $25 |
| Vercel (Pro) | $20 |
| S3 Storage (50GB) | $1.15 |
| **Total** | **~$666/month** |

---

## 6. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         VERCEL                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Next.js Frontend                      │    │
│  │              (Static + Edge Functions)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RAILWAY / RENDER                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  FastAPI Backend                         │    │
│  │              (Python + Celery Workers)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │ Supabase │       │  fal.ai  │       │  OpenAI  │
    │ (DB+Auth)│       │  (AI)    │       │  (LLM)   │
    └──────────┘       └──────────┘       └──────────┘
```

---

## 7. Development Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Foundation | Week 1-2 | Project setup, DB schema, auth |
| Phase 2: Core Pipeline | Week 2-3 | Video analysis, prompt gen, basic generation |
| Phase 3: Face Models | Week 3-4 | LoRA training, InstantID integration |
| Phase 4: Templates | Week 4 | Template system, style library |
| Phase 5: API | Week 4-5 | Complete REST API |
| Phase 6: Frontend | Week 5-6 | Full UI implementation |
| Phase 7: Polish | Week 6-7 | Testing, optimization, edge cases |
| Phase 8: Launch | Week 7-8 | Deployment, monitoring, documentation |

**Total: 8 weeks to MVP**

---

## 8. Key Differentiators from Competitors

1. **Hybrid Face Approach**: Offer both quick single-shot (ThumbMagic style) AND trained LoRA (ThumbnailCreator quality)
2. **Open Prompt Editing**: Let users see and modify the generated prompts
3. **Template Customization**: Allow users to save their own templates
4. **Cost Transparency**: Show users exactly what each generation costs
5. **Local Export**: Support for downloading and editing in external tools

---

## 9. Next Steps

1. Set up development environment with the tech stack above
2. Create Supabase project and configure auth
3. Obtain API keys: fal.ai, OpenAI, YouTube Data API
4. Implement Phase 1 foundation
5. Build and test core video-to-thumbnail pipeline
6. Iterate based on output quality

---

## Appendix: API Keys Required

| Service | Purpose | Where to Get |
|---------|---------|--------------|
| fal.ai | Image generation, LoRA training | https://fal.ai/dashboard/keys |
| OpenAI | Prompt generation | https://platform.openai.com/api-keys |
| YouTube Data API | Video metadata | https://console.cloud.google.com |
| Supabase | Database, auth | https://supabase.com/dashboard |
