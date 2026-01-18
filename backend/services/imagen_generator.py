"""
Google Gemini Image Generator Service
Generates images using Google's Gemini 3 Pro Image Preview model.
"""
import base64
import time
import os
from typing import Optional, List
from google import genai
from google.genai import types


class ImagenGenerator:
    """Generates thumbnail images using Google Gemini 3 Pro Image Preview."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini image generator.

        Args:
            api_key: Google AI API key (uses GOOGLE_AI_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        if not self.api_key:
            raise ValueError("Google AI API key required")

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3-pro-image-preview"

    async def generate_thumbnail(
        self,
        prompt: str,
        num_images: int = 4,
        aspect_ratio: str = "16:9",
        reference_image: Optional[str] = None,
        face_images: Optional[List[str]] = None,
        safety_filter_level: str = "block_low_and_above",
        person_generation: str = "allow_adult",
    ) -> dict:
        """
        Generate thumbnail images using Gemini 3 Pro Image Preview.

        Args:
            prompt: Image generation prompt with video context
            num_images: Number of variations to generate (1-4)
            aspect_ratio: Output aspect ratio (16:9 for thumbnails)
            reference_image: Base64 reference thumbnail - use for FORMAT/LAYOUT only, NOT people
            face_images: List of base64 face photos - these are the ONLY people in the thumbnail
            safety_filter_level: Safety filter threshold
            person_generation: Person generation setting

        Returns:
            Dictionary with images list (base64) and generation_time_ms
        """
        start_time = time.time()

        # Build the prompt with thumbnail optimization
        enhanced_prompt = self._enhance_prompt_for_thumbnails(prompt)

        # Build the content array
        content_parts = []

        # FIRST: Add the reference image for FORMAT/LAYOUT only
        if reference_image:
            print(f"[DEBUG] Including reference thumbnail for FORMAT only")
            ref_bytes = self._decode_base64_image(reference_image)
            if ref_bytes:
                content_parts.append(types.Part.from_bytes(data=ref_bytes, mime_type="image/png"))
                content_parts.append(
                    """REFERENCE THUMBNAIL (FORMAT ONLY):
This image shows the FORMAT/LAYOUT to replicate:
- Copy the EXACT composition, layout, and positioning
- Copy the color scheme, lighting style, and mood
- Copy the text styling and placement
- Copy the pose TYPES and expression TYPES

⚠️ CRITICAL: DO NOT copy any PEOPLE from this reference image.
The people/characters in this reference are just placeholders showing poses.
You must use ONLY the face photos provided below for all people in the thumbnail."""
                )

        # SECOND: Add ALL face photos - these replace ALL characters in the reference
        if face_images and len(face_images) > 0:
            print(f"[DEBUG] Including {len(face_images)} face photo(s) - these are the ONLY people to use")
            content_parts.append(
                f"""FACE PHOTOS ({len(face_images)} provided):
These are the ONLY people who should appear in the final thumbnail.
Use these faces to replace ALL characters/people from the reference format.
Each face can be used for any character position in the layout."""
            )
            for i, face_data in enumerate(face_images):
                face_bytes = self._decode_base64_image(face_data)
                if face_bytes:
                    content_parts.append(types.Part.from_bytes(data=face_bytes, mime_type="image/png"))
                    content_parts.append(f"FACE {i + 1}: Use this person's EXACT face, skin tone, and features.")

        # THIRD: Add the main generation prompt
        generation_prompt = f"""Generate a YouTube thumbnail image with {aspect_ratio} aspect ratio.

VIDEO CONTEXT:
{enhanced_prompt}

GENERATION RULES:
1. Use the REFERENCE FORMAT above for layout, composition, colors, poses, and style
2. Use ONLY the FACE PHOTOS above as the people - DO NOT use anyone from the reference
3. The faces provided can fill ANY/ALL character positions in the format
4. Apply the pose types and expression types from the reference to the provided faces
5. Adapt the content (text, graphics) to match the video context
6. Maintain professional YouTube thumbnail quality

⚠️ ABSOLUTE RULE: No person from the reference image should appear. Only the provided face photos."""

        content_parts.append(generation_prompt)

        try:
            images = []

            # Generate multiple images by making multiple requests
            for i in range(min(num_images, 4)):
                print(f"[DEBUG] Generating image {i + 1}/{num_images}")

                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=content_parts,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE", "TEXT"],
                            safety_settings=[
                                types.SafetySetting(
                                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                                    threshold="BLOCK_NONE",
                                ),
                                types.SafetySetting(
                                    category="HARM_CATEGORY_HARASSMENT",
                                    threshold="BLOCK_NONE",
                                ),
                                types.SafetySetting(
                                    category="HARM_CATEGORY_HATE_SPEECH",
                                    threshold="BLOCK_NONE",
                                ),
                                types.SafetySetting(
                                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                    threshold="BLOCK_ONLY_HIGH",
                                ),
                            ],
                        ),
                    )

                    # Extract image from response
                    if response.candidates and len(response.candidates) > 0:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            for part in candidate.content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    mime_type = part.inline_data.mime_type
                                    image_bytes = part.inline_data.data
                                    if isinstance(image_bytes, bytes):
                                        b64_data = base64.b64encode(image_bytes).decode('utf-8')
                                    else:
                                        b64_data = image_bytes
                                    images.append(f"data:{mime_type};base64,{b64_data}")
                                    break

                except Exception as gen_error:
                    error_str = str(gen_error)
                    print(f"[WARNING] Image {i + 1} generation error: {error_str}")

                    # Check for safety-related errors
                    if "IMAGE_SAFETY" in error_str or "safety" in error_str.lower():
                        print(f"[WARNING] Safety filter triggered. Trying without face images...")
                        # Try generating without face images as fallback
                        try:
                            fallback_response = self.client.models.generate_content(
                                model=self.model,
                                contents=[generation_prompt],  # Just the text prompt
                                config=types.GenerateContentConfig(
                                    response_modalities=["IMAGE", "TEXT"],
                                ),
                            )
                            if fallback_response.candidates and len(fallback_response.candidates) > 0:
                                candidate = fallback_response.candidates[0]
                                if hasattr(candidate, 'content') and candidate.content:
                                    for part in candidate.content.parts:
                                        if hasattr(part, 'inline_data') and part.inline_data:
                                            mime_type = part.inline_data.mime_type
                                            image_bytes = part.inline_data.data
                                            if isinstance(image_bytes, bytes):
                                                b64_data = base64.b64encode(image_bytes).decode('utf-8')
                                            else:
                                                b64_data = image_bytes
                                            images.append(f"data:{mime_type};base64,{b64_data}")
                                            print(f"[DEBUG] Fallback image {i + 1} generated successfully")
                                            break
                        except Exception as fallback_error:
                            print(f"[ERROR] Fallback also failed: {fallback_error}")
                            continue
                    else:
                        # For other errors, just continue to next attempt
                        continue

            generation_time_ms = int((time.time() - start_time) * 1000)

            if not images:
                raise ValueError("No images generated. The safety filter may have blocked the request. Try different face photos or a simpler prompt.")

            return {
                "images": images,
                "generation_time_ms": generation_time_ms,
            }

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Image generation failed: {str(e)}")

    def _decode_base64_image(self, image_data: str) -> Optional[bytes]:
        """Decode base64 image data to bytes."""
        try:
            if image_data.startswith('data:'):
                # Remove data URI prefix
                image_data = image_data.split(',')[1]
            return base64.b64decode(image_data)
        except Exception as e:
            print(f"[ERROR] Failed to decode image: {e}")
            return None

    def _enhance_prompt_for_thumbnails(self, prompt: str) -> str:
        """
        Enhance the prompt for better YouTube thumbnail results.

        Args:
            prompt: Original prompt

        Returns:
            Enhanced prompt optimized for thumbnails
        """
        # Add thumbnail-specific quality modifiers if not present
        quality_terms = [
            "high quality",
            "professional",
            "vibrant colors",
            "sharp focus",
            "eye-catching",
        ]

        prompt_lower = prompt.lower()
        enhancements = []

        for term in quality_terms:
            if term not in prompt_lower:
                enhancements.append(term)

        # Add YouTube thumbnail specific guidance
        if "thumbnail" not in prompt_lower:
            enhancements.append("YouTube thumbnail style")

        if enhancements:
            return f"{prompt}, {', '.join(enhancements)}"
        return prompt

    async def generate_with_reference_image(
        self,
        prompt: str,
        reference_image_base64: str,
        num_images: int = 4,
        aspect_ratio: str = "16:9",
    ) -> dict:
        """
        Generate images using a reference image for style/content guidance.
        Uses Imagen's edit capability to maintain consistency.

        Args:
            prompt: Generation prompt
            reference_image_base64: Base64 encoded reference image
            num_images: Number of variations
            aspect_ratio: Output aspect ratio

        Returns:
            Dictionary with images list and generation_time_ms
        """
        start_time = time.time()

        try:
            # Decode the reference image
            if reference_image_base64.startswith('data:'):
                # Remove data URI prefix
                reference_image_base64 = reference_image_base64.split(',')[1]

            reference_bytes = base64.b64decode(reference_image_base64)

            # Use image editing to incorporate reference
            response = self.client.models.edit_image(
                model="imagen-3.0-capability-001",
                prompt=prompt,
                reference_images=[
                    types.RawReferenceImage(
                        reference_image=types.Image(image_bytes=reference_bytes),
                        reference_id=0,
                    )
                ],
                config=types.EditImageConfig(
                    number_of_images=min(num_images, 4),
                    edit_mode="EDIT_MODE_INPAINT_INSERTION",
                ),
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            images = []
            for generated_image in response.generated_images:
                if generated_image.image and generated_image.image.image_bytes:
                    b64_data = base64.b64encode(generated_image.image.image_bytes).decode('utf-8')
                    images.append(f"data:image/png;base64,{b64_data}")

            return {
                "images": images,
                "generation_time_ms": generation_time_ms,
            }

        except Exception as e:
            raise ValueError(f"Reference image generation failed: {str(e)}")

    async def upscale(
        self,
        image_base64: str,
        upscale_factor: int = 2,
    ) -> dict:
        """
        Upscale an image for higher resolution output.

        Args:
            image_base64: Base64 encoded image to upscale
            upscale_factor: Upscale factor (2 or 4)

        Returns:
            Dictionary with upscaled image base64
        """
        start_time = time.time()

        try:
            if image_base64.startswith('data:'):
                image_base64 = image_base64.split(',')[1]

            image_bytes = base64.b64decode(image_base64)

            response = self.client.models.upscale_image(
                model="imagen-3.0-generate-001",
                image=types.Image(image_bytes=image_bytes),
                config=types.UpscaleImageConfig(
                    upscale_factor=f"x{upscale_factor}",
                ),
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            if response.generated_images and response.generated_images[0].image:
                b64_data = base64.b64encode(
                    response.generated_images[0].image.image_bytes
                ).decode('utf-8')
                return {
                    "image": f"data:image/png;base64,{b64_data}",
                    "generation_time_ms": generation_time_ms,
                }

            raise ValueError("Upscaling returned no result")

        except Exception as e:
            raise ValueError(f"Upscaling failed: {str(e)}")
