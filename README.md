# AI Thumbnail Generator

AI-powered YouTube thumbnail generator that creates professional, viral-style thumbnails.

## Features

- **YouTube URL Analysis** - Paste a URL, get context-aware thumbnails
- **Custom Prompts** - Write your own prompt for creative control
- **Reference Images** - Upload thumbnails to match their style
- **Multi-Face Support** - Upload multiple face photos:
  - **First photo** = Primary person (main character, reactor)
  - **Additional photos** = Secondary people (replace other faces in reference)
  - AI analyzes ALL faces individually and uses them in the thumbnail
- **Style Templates** - MrBeast, Educational, Tech, Minimalist styles
- **Text Overlay** - Automatic eye-catching text generation
- **4 Variations** - Each generation produces 4 options
- **Easy Download** - Click to download thumbnails (works with base64 images)

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- API Keys: Google AI, OpenAI, YouTube Data API

### Setup

**1. Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Edit with your API keys
python main.py            # Runs on :8000
```

**2. Frontend**
```bash
cd frontend
npm install
npm run dev               # Runs on :3000
```

**3. Open** http://localhost:3000

## API Keys Required

| Service | Purpose | Get Key |
|---------|---------|---------|
| Google AI | Image generation | https://aistudio.google.com/apikey |
| OpenAI | Prompt generation | https://platform.openai.com/api-keys |
| YouTube | Video metadata | https://console.cloud.google.com |

## Project Structure

```
ThumbnailMaker/
├── frontend/                 # Next.js 16 + React 19 + Tailwind
│   └── src/
│       ├── app/page.tsx      # Main UI
│       ├── components/       # Uploaders
│       ├── stores/           # Zustand state
│       └── services/api.ts   # Backend client
│
├── backend/                  # Python FastAPI
│   ├── main.py               # API endpoints
│   ├── config.py             # Settings
│   └── services/
│       ├── video_analyzer.py     # YouTube analysis
│       ├── prompt_generator.py   # GPT-4o prompts
│       ├── imagen_generator.py   # Google Imagen
│       ├── reference_analyzer.py # Style analysis
│       └── text_overlay.py       # Pillow text
│
├── README.md
├── BUILD_INSTRUCTIONS.md     # Full replication guide
└── IMPLEMENTATION_PLAN.md    # Architecture details
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/templates` | GET | List style templates |
| `/generate/from-url` | POST | Generate from YouTube URL |
| `/generate/from-prompt` | POST | Generate from custom prompt |

## How It Works

```
YouTube URL → Extract title, description, transcript
     ↓
Reference Images → Analyze exact style, composition, colors with GPT-4o Vision
     ↓
Face Photos → Analyze EACH face individually:
             - Photo 1 = PRIMARY (main character/reactor)
             - Photo 2+ = SECONDARY (replace other people in reference)
     ↓
Prompt Generation → GPT-4o creates prompt using ALL face descriptions
     ↓
Image Generation → Google Imagen creates 4 thumbnails with all faces
     ↓
Text Overlay → Pillow adds gradient + text
     ↓
Results → Display in gallery, click to download
```

## Cost Per Generation

| Service | Cost |
|---------|------|
| Google Imagen (4 images) | ~$0.04 |
| OpenAI GPT-4o | ~$0.01 |
| YouTube API | FREE |
| **Total** | **~$0.05** |

## Replication Guide

See **[BUILD_INSTRUCTIONS.md](./BUILD_INSTRUCTIONS.md)** for complete step-by-step instructions to recreate this application from scratch.

## License

MIT
