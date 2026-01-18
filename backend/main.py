"""
AI Thumbnail Generator - FastAPI Backend
Main application entry point.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import os

from config import settings
from models import (
    VideoURLRequest,
    PromptRequest,
    InpaintRequest,
    TextOverlayRequest,
    FaceModelTrainingRequest,
    ThumbnailResponse,
    VideoAnalysisResponse,
    FaceModelResponse,
    TemplateResponse,
    HealthResponse,
)
from services import (
    VideoAnalyzer,
    PromptGenerator,
    ImageGenerator,
    ImagenGenerator,
    TextOverlayService,
    LoRATrainer,
    ReferenceAnalyzer,
)


# ============================================
# Application Lifespan
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup: Initialize services
    app.state.video_analyzer = VideoAnalyzer(settings.youtube_api_key)
    app.state.prompt_generator = PromptGenerator(settings.openai_api_key)
    app.state.reference_analyzer = ReferenceAnalyzer(settings.openai_api_key)
    app.state.image_generator = ImageGenerator()  # FLUX (fallback)
    app.state.text_overlay = TextOverlayService()

    # Initialize Imagen generator if API key is available
    if settings.google_ai_api_key:
        try:
            app.state.imagen_generator = ImagenGenerator(settings.google_ai_api_key)
            print("Google Imagen generator initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Imagen generator: {e}")
            app.state.imagen_generator = None
    else:
        app.state.imagen_generator = None
        print("Google AI API key not configured, using FLUX only")

    app.state.lora_trainer = LoRATrainer(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key
    )

    yield

    # Shutdown: Cleanup if needed
    pass


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="AI-powered YouTube thumbnail generation API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Dependency Injection Helpers
# ============================================

def get_video_analyzer() -> VideoAnalyzer:
    return app.state.video_analyzer


def get_prompt_generator() -> PromptGenerator:
    return app.state.prompt_generator


def get_reference_analyzer() -> ReferenceAnalyzer:
    return app.state.reference_analyzer


def get_image_generator() -> ImageGenerator:
    return app.state.image_generator


def get_lora_trainer() -> LoRATrainer:
    return app.state.lora_trainer


def get_imagen_generator() -> Optional[ImagenGenerator]:
    return getattr(app.state, 'imagen_generator', None)


def get_text_overlay() -> TextOverlayService:
    return app.state.text_overlay


# ============================================
# Health & Info Endpoints
# ============================================

@app.get("/", response_model=HealthResponse)
async def root():
    """API root - health check."""
    return HealthResponse(status="healthy", version=settings.api_version)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version=settings.api_version)


# ============================================
# Template Endpoints
# ============================================

# Templates stored in memory for now (loaded from DB in production)
TEMPLATES = {
    "mrbeast": {
        "id": "mrbeast",
        "name": "Viral/MrBeast Style",
        "category": "entertainment",
        "description": "High-energy, viral-style thumbnails with extreme expressions and bold colors",
    },
    "educational": {
        "id": "educational",
        "name": "Educational/Explainer",
        "category": "education",
        "description": "Professional, authoritative thumbnails for educational content",
    },
    "tech": {
        "id": "tech",
        "name": "Tech/Product Review",
        "category": "technology",
        "description": "Sleek, modern thumbnails for tech and product content",
    },
    "controversy": {
        "id": "controversy",
        "name": "Drama/Controversy",
        "category": "entertainment",
        "description": "Tension-filled, dramatic thumbnails for controversial content",
    },
    "minimalist": {
        "id": "minimalist",
        "name": "Clean/Minimalist",
        "category": "lifestyle",
        "description": "Clean, aesthetic thumbnails for lifestyle content",
    },
}


@app.get("/templates", response_model=list[TemplateResponse])
async def get_templates():
    """Get all available thumbnail templates."""
    return [TemplateResponse(**t) for t in TEMPLATES.values()]


@app.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str):
    """Get a specific template by ID."""
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse(**TEMPLATES[template_id])


# ============================================
# Video Analysis Endpoints
# ============================================

@app.post("/analyze-video", response_model=VideoAnalysisResponse)
async def analyze_video(
    url: str,
    video_analyzer: VideoAnalyzer = Depends(get_video_analyzer)
):
    """Analyze a YouTube video and extract metadata + transcript."""
    try:
        data = video_analyzer.analyze(url)
        return VideoAnalysisResponse(
            video_id=data["video_id"],
            title=data["title"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            channel=data.get("channel", ""),
            transcript=data.get("transcript"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze video: {str(e)}")


# ============================================
# Generation Endpoints
# ============================================

@app.post("/generate/from-url", response_model=ThumbnailResponse)
async def generate_from_url(
    request: VideoURLRequest,
    video_analyzer: VideoAnalyzer = Depends(get_video_analyzer),
    prompt_generator: PromptGenerator = Depends(get_prompt_generator),
    reference_analyzer: ReferenceAnalyzer = Depends(get_reference_analyzer),
    image_generator: ImageGenerator = Depends(get_image_generator),
    imagen_generator: Optional[ImagenGenerator] = Depends(get_imagen_generator),
    text_overlay: TextOverlayService = Depends(get_text_overlay),
    lora_trainer: LoRATrainer = Depends(get_lora_trainer),
):
    """Generate thumbnails from a YouTube URL."""
    import traceback
    try:
        print(f"[DEBUG] Starting generation for URL: {request.url}")
        # Step 1: Analyze video to get context
        print(f"[DEBUG] Step 1: Analyzing YouTube video for context...")
        video_data = video_analyzer.analyze(request.url)
        print(f"[DEBUG] Video context extracted:")
        print(f"  - Title: {video_data.get('title', 'N/A')}")
        print(f"  - Channel: {video_data.get('channel', 'N/A')}")
        print(f"  - Tags: {video_data.get('tags', [])[:5]}")
        print(f"  - Description: {video_data.get('description', 'N/A')[:200]}...")
        print(f"  - Transcript available: {'Yes' if video_data.get('transcript') else 'No'}")

        # Step 2: Get face model if specified (for FLUX only)
        lora_url = None
        trigger_word = "person"

        if request.face_model_id:
            model = await lora_trainer.get_training_status(request.face_model_id)
            if model and model.get("training_status") == "completed":
                lora_url = model.get("lora_url")
                trigger_word = model.get("trigger_word", "person")

        # Step 3: Analyze reference thumbnails if provided
        reference_analysis = None
        if request.reference_thumbnails and len(request.reference_thumbnails) > 0:
            try:
                print(f"[DEBUG] Analyzing {len(request.reference_thumbnails)} reference thumbnail(s)...")
                reference_data = [{"data": ref.data, "description": ref.description} for ref in request.reference_thumbnails]
                reference_analysis = reference_analyzer.analyze_reference_thumbnails(reference_data)
                print(f"[DEBUG] Reference analysis complete:")
                print(f"  - Composition: {reference_analysis.get('composition', {})}")
                print(f"  - Colors: {reference_analysis.get('colors', {})}")
                print(f"  - Mood: {reference_analysis.get('mood', 'N/A')}")
            except Exception as e:
                print(f"[ERROR] Failed to analyze reference thumbnails: {e}")
                import traceback
                traceback.print_exc()
                reference_analysis = None

        # Step 4: Analyze face photos if provided
        face_description = None
        face_photos_data = None  # List of (data, name) tuples for imagen_generator
        if request.face_images and len(request.face_images) > 0:
            try:
                print(f"[DEBUG] Analyzing {len(request.face_images)} face photo(s)...")
                # Extract just the base64 data for analysis
                face_data_list = [photo.data for photo in request.face_images]
                face_description = reference_analyzer.analyze_face_photos(face_data_list)
                # Prepare face photos with names for imagen_generator
                face_photos_data = [(photo.data, photo.name) for photo in request.face_images]
                print(f"[DEBUG] Face photos: {[name for _, name in face_photos_data]}")
                print(f"[DEBUG] Face description: {face_description}")
            except Exception as e:
                print(f"[ERROR] Failed to analyze face photos: {e}")
                import traceback
                traceback.print_exc()
                face_description = None
                face_photos_data = None

        # Step 5: Get template system prompt if specified
        template_prompt = None
        if request.template_id and request.template_id in TEMPLATES:
            # Would fetch from database in production
            pass

        # Step 6: Generate prompt with reference style guidance
        prompt_data = prompt_generator.generate_prompt(
            video_data,
            template_system_prompt=template_prompt,
            trigger_word=trigger_word,
            reference_analysis=reference_analysis,
            face_description=face_description,
        )

        # Step 7: Generate images using Imagen (preferred) or FLUX as fallback
        print(f"[DEBUG] Final prompt for image generation:")
        print(f"  {prompt_data['prompt'][:500]}...")
        print(f"[DEBUG] Thumbnail text: {prompt_data.get('thumbnail_text', 'N/A')}")

        if imagen_generator is not None:
            print(f"[DEBUG] Using Gemini for generation")

            # Get reference image for FORMAT (but instruct Gemini not to copy people)
            reference_image = None
            if request.reference_thumbnails and len(request.reference_thumbnails) > 0:
                reference_image = request.reference_thumbnails[0].data
                print(f"[DEBUG] Passing reference thumbnail for FORMAT only (not people)")

            if face_photos_data and len(face_photos_data) > 0:
                print(f"[DEBUG] Passing {len(face_photos_data)} face photo(s) - these replace ALL characters")

            result = await imagen_generator.generate_thumbnail(
                prompt=prompt_data["prompt"],
                num_images=request.num_variations,
                reference_image=reference_image,  # For FORMAT only
                face_photos=face_photos_data,  # ALL faces with names for ALL characters
            )
        else:
            print(f"[DEBUG] Using FLUX for generation (Imagen not available)")
            result = await image_generator.generate_thumbnail(
                prompt=prompt_data["prompt"],
                lora_url=lora_url,
                num_images=request.num_variations
            )

        # Step 6: Add text overlay if thumbnail_text was generated
        thumbnail_text = prompt_data.get("thumbnail_text", "")
        final_images = result["images"]

        if thumbnail_text and request.add_text_overlay:
            final_images = []
            for img in result["images"]:
                # Add gradient background for readability
                img_with_gradient = text_overlay.add_gradient_background(
                    img, position="bottom", opacity=0.5, height_ratio=0.35
                )
                # Add the text
                img_with_text = text_overlay.add_text(
                    image_data=img_with_gradient,
                    text=thumbnail_text.upper(),
                    position="bottom_center",
                    font_preset="impact",
                    color_preset="white_shadow",
                    stroke_width=5,
                    shadow_offset=4,
                )
                final_images.append(img_with_text)

        return ThumbnailResponse(
            images=final_images,
            prompt_used=prompt_data["prompt"],
            thumbnail_text=thumbnail_text,
            generation_time_ms=result.get("generation_time_ms"),
        )

    except ValueError as e:
        print(f"[ERROR] ValueError: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/generate/from-prompt", response_model=ThumbnailResponse)
async def generate_from_prompt(
    request: PromptRequest,
    reference_analyzer: ReferenceAnalyzer = Depends(get_reference_analyzer),
    image_generator: ImageGenerator = Depends(get_image_generator),
    imagen_generator: Optional[ImagenGenerator] = Depends(get_imagen_generator),
    text_overlay: TextOverlayService = Depends(get_text_overlay),
    lora_trainer: LoRATrainer = Depends(get_lora_trainer),
):
    """Generate thumbnails from a custom prompt."""
    try:
        lora_url = None

        # Get face model if specified
        if request.face_model_id:
            model = await lora_trainer.get_training_status(request.face_model_id)
            if model and model.get("training_status") == "completed":
                lora_url = model.get("lora_url")

        # Analyze reference thumbnails if provided
        reference_analysis = None
        if request.reference_thumbnails and len(request.reference_thumbnails) > 0:
            try:
                reference_data = [{"data": ref.data, "description": ref.description} for ref in request.reference_thumbnails]
                reference_analysis = reference_analyzer.analyze_reference_thumbnails(reference_data)
            except Exception as e:
                print(f"Warning: Failed to analyze reference thumbnails: {e}")
                reference_analysis = None

        # Analyze face photos if provided
        face_description = None
        face_photos_data = None  # List of (data, name) tuples for imagen_generator
        if request.face_images and len(request.face_images) > 0:
            try:
                # Extract just the base64 data for analysis
                face_data_list = [photo.data for photo in request.face_images]
                face_description = reference_analyzer.analyze_face_photos(face_data_list)
                # Prepare face photos with names for imagen_generator
                face_photos_data = [(photo.data, photo.name) for photo in request.face_images]
            except Exception as e:
                print(f"Warning: Failed to analyze face photos: {e}")
                face_description = None
                face_photos_data = None

        # Enhance prompt with reference style if analysis available
        enhanced_prompt = request.prompt
        if reference_analysis or face_description:
            enhanced_prompt = reference_analyzer.generate_style_enhanced_prompt(
                base_prompt=request.prompt,
                reference_analysis=reference_analysis,
                face_description=face_description,
            )

        # Generate images using Imagen (preferred) or FLUX as fallback
        if imagen_generator is not None:
            print(f"[DEBUG] Using Gemini for generation (from prompt)")

            # Get reference image for FORMAT
            reference_image = None
            if request.reference_thumbnails and len(request.reference_thumbnails) > 0:
                reference_image = request.reference_thumbnails[0].data
                print(f"[DEBUG] Passing reference thumbnail for FORMAT only")

            if face_photos_data and len(face_photos_data) > 0:
                print(f"[DEBUG] Passing {len(face_photos_data)} face photo(s) - replace ALL characters")

            result = await imagen_generator.generate_thumbnail(
                prompt=enhanced_prompt,
                num_images=request.num_variations,
                reference_image=reference_image,
                face_photos=face_photos_data,  # ALL faces with names for ALL characters
            )
        else:
            print(f"[DEBUG] Using FLUX for generation (Imagen not available)")
            result = await image_generator.generate_thumbnail(
                prompt=enhanced_prompt,
                lora_url=lora_url,
                num_images=request.num_variations,
            )

        # Add text overlay if requested
        thumbnail_text = request.thumbnail_text
        final_images = result["images"]

        if thumbnail_text and request.add_text_overlay:
            text_cfg = request.text_config or {}
            final_images = []
            for img in result["images"]:
                # Add gradient background for readability
                img_with_gradient = text_overlay.add_gradient_background(
                    img, position="bottom", opacity=0.5, height_ratio=0.35
                )
                # Add the text
                img_with_text = text_overlay.add_text(
                    image_data=img_with_gradient,
                    text=thumbnail_text.upper(),
                    position=text_cfg.get("position", "bottom_center") if isinstance(text_cfg, dict) else getattr(text_cfg, "position", "bottom_center"),
                    font_preset=text_cfg.get("font_preset", "impact") if isinstance(text_cfg, dict) else getattr(text_cfg, "font_preset", "impact"),
                    color_preset=text_cfg.get("color_preset", "white_shadow") if isinstance(text_cfg, dict) else getattr(text_cfg, "color_preset", "white_shadow"),
                    font_size=text_cfg.get("font_size") if isinstance(text_cfg, dict) else getattr(text_cfg, "font_size", None),
                )
                final_images.append(img_with_text)

        return ThumbnailResponse(
            images=final_images,
            prompt_used=enhanced_prompt,
            thumbnail_text=thumbnail_text,
            generation_time_ms=result.get("generation_time_ms"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/inpaint")
async def inpaint_image(
    request: InpaintRequest,
    image_generator: ImageGenerator = Depends(get_image_generator),
):
    """Inpaint/edit a region of an image."""
    try:
        result = await image_generator.inpaint(
            image_url=request.image_url,
            mask_url=request.mask_url,
            prompt=request.prompt,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inpainting failed: {str(e)}")


@app.post("/text-overlay")
async def add_text_overlay(
    request: TextOverlayRequest,
    text_overlay: TextOverlayService = Depends(get_text_overlay),
):
    """Add text overlay to an image."""
    try:
        image_data = request.image_data

        # Add gradient background if requested
        if request.add_gradient:
            image_data = text_overlay.add_gradient_background(
                image_data,
                position="bottom",
                opacity=0.5,
                height_ratio=0.35,
            )

        # Add text overlay
        result_image = text_overlay.add_text(
            image_data=image_data,
            text=request.text.upper(),
            position=request.position,
            font_preset=request.font_preset,
            color_preset=request.color_preset,
            font_size=request.font_size,
        )

        return {"image": result_image}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text overlay failed: {str(e)}")


# ============================================
# Face Model Endpoints
# ============================================

@app.post("/face-models/train")
async def train_face_model(
    request: FaceModelTrainingRequest,
    background_tasks: BackgroundTasks,
    lora_trainer: LoRATrainer = Depends(get_lora_trainer),
    user_id: str = "demo-user",  # Would come from auth in production
):
    """Start LoRA training for a face model."""
    try:
        # Run training in background
        background_tasks.add_task(
            lora_trainer.start_training,
            user_id,
            request.images_zip_url,
            request.name,
        )

        return {
            "status": "training_started",
            "message": "Training started. This typically takes 15-20 minutes.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")


@app.get("/face-models", response_model=list[FaceModelResponse])
async def list_face_models(
    lora_trainer: LoRATrainer = Depends(get_lora_trainer),
    user_id: str = "demo-user",  # Would come from auth
):
    """List user's trained face models."""
    try:
        models = await lora_trainer.list_user_models(user_id)
        return [
            FaceModelResponse(
                id=m["id"],
                name=m["name"],
                trigger_word=m["trigger_word"],
                status=m["training_status"],
                lora_url=m.get("lora_url"),
                created_at=m["created_at"],
            )
            for m in models
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/face-models/{model_id}")
async def get_face_model(
    model_id: str,
    lora_trainer: LoRATrainer = Depends(get_lora_trainer),
):
    """Get a specific face model status."""
    try:
        model = await lora_trainer.get_training_status(model_id)
        return model
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/face-models/{model_id}")
async def delete_face_model(
    model_id: str,
    lora_trainer: LoRATrainer = Depends(get_lora_trainer),
    user_id: str = "demo-user",
):
    """Delete a face model."""
    try:
        await lora_trainer.delete_model(model_id, user_id)
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# Run with Uvicorn
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
