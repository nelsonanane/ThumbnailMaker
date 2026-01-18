# AI Thumbnail Generator

AI-powered YouTube thumbnail generator that creates professional, viral-style thumbnails.

## Features

- **YouTube URL Analysis** - Paste a URL, get context-aware thumbnails
- **Custom Prompts** - Write your own prompt for creative control
- **Reference Images** - Upload thumbnails to match their style
- **Face Photos** - Upload faces to replace characters in the reference format
  - All uploaded faces are used in the thumbnail
  - Face 1 replaces character position 1, Face 2 replaces position 2, etc.
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
1. INPUTS:
   YouTube URL    → Video context (title, description, transcript)
   Reference      → FORMAT only (layout, poses, colors) - analyzed as TEXT
   Face Photos    → The ONLY people who will appear in the thumbnail

2. ANALYSIS (GPT-4o Vision):
   Reference      → Extracts FORMAT as text (layout, pose types, expression types, colors)
   Face Photos    → Describes each face in detail

3. PROMPT GENERATION:
   Combines FORMAT description + Face descriptions + Video topic
   (Reference image is NOT passed to the generator - only its FORMAT as text)

4. IMAGE GENERATION (Gemini):
   Receives: TEXT prompt + Face IMAGES only
   Creates thumbnails using YOUR faces in the reference FORMAT
   Characters from reference NEVER appear - only your face photos

5. OUTPUT:
   4 thumbnail variations + Text overlay
```

**Key Point:** The reference image is analyzed for FORMAT only (as text). It is NEVER sent to the image generator. Only face photos are sent, ensuring no characters from the reference appear in your thumbnails.

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
