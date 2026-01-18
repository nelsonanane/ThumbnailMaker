"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from enum import Enum


class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TrainingStatus(str, Enum):
    PENDING = "pending"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    THUMBNAIL = "thumbnail"
    FACE_TRAINING = "face_training"
    INPAINT = "inpaint"


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================
# Request Models
# ============================================

class TextOverlayConfig(BaseModel):
    """Configuration for text overlay."""
    text: Optional[str] = Field(None, description="Custom text (uses generated text if None)")
    position: str = Field("bottom_center", description="Text position preset")
    font_preset: str = Field("impact", description="Font style preset")
    color_preset: str = Field("white_shadow", description="Color scheme preset")
    font_size: Optional[int] = Field(None, description="Override font size")


class ReferenceImage(BaseModel):
    """A reference image with its base64 data."""
    data: str = Field(..., description="Base64 encoded image data (with or without data URI prefix)")
    description: Optional[str] = Field(None, description="Optional user-provided description")


class FacePhotoWithName(BaseModel):
    """A face photo with its name for prompt labeling."""
    data: str = Field(..., description="Base64 encoded image data")
    name: str = Field(..., description="Original file name for labeling in prompts")


class VideoURLRequest(BaseModel):
    """Request to generate thumbnail from YouTube URL."""
    url: str = Field(..., description="YouTube video URL")
    template_id: Optional[str] = Field(None, description="Template style to use")
    face_model_id: Optional[str] = Field(None, description="Trained face model ID")
    face_images: Optional[List[FacePhotoWithName]] = Field(None, description="Face photos with names for prompt labeling")
    reference_thumbnails: Optional[List[ReferenceImage]] = Field(None, description="Reference thumbnail examples to analyze")
    num_variations: int = Field(4, ge=1, le=8, description="Number of variations")
    add_text_overlay: bool = Field(True, description="Add text overlay to thumbnails")
    text_config: Optional[TextOverlayConfig] = Field(None, description="Text overlay configuration")


class PromptRequest(BaseModel):
    """Request to generate thumbnail from custom prompt."""
    prompt: str = Field(..., min_length=10, description="Image generation prompt")
    template_id: Optional[str] = Field(None, description="Template style to use")
    face_model_id: Optional[str] = Field(None, description="Trained face model ID")
    face_image_url: Optional[str] = Field(None, description="Single-shot face image URL")
    face_images: Optional[List[FacePhotoWithName]] = Field(None, description="Face photos with names for prompt labeling")
    reference_thumbnails: Optional[List[ReferenceImage]] = Field(None, description="Reference thumbnail examples to analyze")
    num_variations: int = Field(4, ge=1, le=8, description="Number of variations")
    add_text_overlay: bool = Field(False, description="Add text overlay to thumbnails")
    thumbnail_text: Optional[str] = Field(None, description="Text to overlay on thumbnails")
    text_config: Optional[TextOverlayConfig] = Field(None, description="Text overlay configuration")


class InpaintRequest(BaseModel):
    """Request to inpaint/edit part of an image."""
    image_url: str = Field(..., description="Original image URL")
    mask_url: str = Field(..., description="Mask image URL (white = edit area)")
    prompt: str = Field(..., description="What to generate in the masked area")


class TextOverlayRequest(BaseModel):
    """Request to add text overlay to an image."""
    image_data: str = Field(..., description="Base64 encoded image or data URI")
    text: str = Field(..., min_length=1, description="Text to overlay")
    position: str = Field("bottom_center", description="Position preset")
    font_preset: str = Field("impact", description="Font style preset")
    color_preset: str = Field("white_shadow", description="Color scheme preset")
    font_size: Optional[int] = Field(None, description="Override font size")
    add_gradient: bool = Field(True, description="Add gradient background for readability")


class FaceModelTrainingRequest(BaseModel):
    """Request to train a new face model."""
    name: str = Field(..., min_length=1, max_length=100, description="Model name")
    images_zip_url: str = Field(..., description="URL to ZIP file of training images")


# ============================================
# Response Models
# ============================================

class ThumbnailResponse(BaseModel):
    """Response containing generated thumbnails."""
    images: List[str] = Field(..., description="List of generated image URLs")
    prompt_used: str = Field(..., description="The prompt used for generation")
    thumbnail_text: Optional[str] = Field(None, description="Suggested text overlay")
    generation_time_ms: Optional[int] = Field(None, description="Generation time in ms")


class VideoAnalysisResponse(BaseModel):
    """Response containing video analysis data."""
    video_id: str
    title: str
    description: str
    tags: List[str]
    channel: str
    transcript: Optional[str] = None


class FaceModelResponse(BaseModel):
    """Response containing face model information."""
    id: str
    name: str
    trigger_word: str
    status: TrainingStatus
    lora_url: Optional[str] = None
    created_at: str


class TemplateResponse(BaseModel):
    """Response containing template information."""
    id: str
    name: str
    category: str
    description: Optional[str] = None


class PromptGenerationResponse(BaseModel):
    """Response from prompt generation."""
    prompt: str
    thumbnail_text: str
    emotion: str
    composition: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str


class ReferenceAnalysisResponse(BaseModel):
    """Response from analyzing reference thumbnails."""
    style_description: str = Field(..., description="Overall style analysis of the reference thumbnails")
    common_elements: List[str] = Field(..., description="Common elements found across references")
    color_palette: str = Field(..., description="Dominant color palette description")
    composition_style: str = Field(..., description="Composition and layout style")
    text_style: Optional[str] = Field(None, description="Text styling if present")
    recommendations: str = Field(..., description="Recommendations for generating similar thumbnails")
