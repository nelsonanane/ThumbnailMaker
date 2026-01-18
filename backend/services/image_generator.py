"""
Image Generator Service
Generates images using fal.ai FLUX API.
"""
import time
from typing import Optional, List
import fal_client


class ImageGenerator:
    """Generates thumbnail images using FLUX via fal.ai."""

    def __init__(self):
        """
        Initialize the image generator.
        fal_client uses FAL_KEY environment variable automatically.
        """
        pass

    async def generate_thumbnail(
        self,
        prompt: str,
        lora_url: Optional[str] = None,
        lora_scale: float = 1.0,
        num_images: int = 4,
        image_size: str = "landscape_16_9",
        guidance_scale: float = 3.5,
        num_inference_steps: int = 28,
    ) -> dict:
        """
        Generate thumbnail images using FLUX.

        Args:
            prompt: Image generation prompt
            lora_url: Optional URL to trained LoRA weights
            lora_scale: LoRA influence strength (0.0-1.0)
            num_images: Number of variations to generate (1-8)
            image_size: Output size preset (landscape_16_9 for thumbnails)
            guidance_scale: How closely to follow prompt (3.5 optimal for FLUX)
            num_inference_steps: Quality vs speed tradeoff (28 is balanced)

        Returns:
            Dictionary with images list and generation_time_ms
        """
        start_time = time.time()

        arguments = {
            "prompt": prompt,
            "image_size": image_size,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "num_images": num_images,
            "enable_safety_checker": True,
        }

        # Add LoRA if provided (trained face model)
        if lora_url:
            arguments["loras"] = [{"path": lora_url, "scale": lora_scale}]
            endpoint = "fal-ai/flux-lora"
        else:
            endpoint = "fal-ai/flux/dev"

        result = await fal_client.run_async(endpoint, arguments=arguments)

        generation_time_ms = int((time.time() - start_time) * 1000)

        if result is None:
            raise ValueError("Image generation returned no result")

        images = result.get("images", [])
        if not images:
            raise ValueError("No images generated")

        return {
            "images": [img["url"] for img in images],
            "generation_time_ms": generation_time_ms,
            "seed": result.get("seed"),
        }

    async def generate_with_face_reference(
        self,
        prompt: str,
        face_image_url: str,
        num_images: int = 4,
        image_size: str = "landscape_16_9",
    ) -> dict:
        """
        Generate with single-shot face consistency using PuLID.

        Uses face image as reference without LoRA training.
        Falls back to regular FLUX if PuLID fails.

        Args:
            prompt: Image generation prompt
            face_image_url: URL to reference face image
            num_images: Number of variations
            image_size: Output size preset

        Returns:
            Dictionary with images list and generation_time_ms
        """
        start_time = time.time()

        try:
            # Use PuLID for face identity preservation
            result = await fal_client.run_async(
                "fal-ai/pulid",
                arguments={
                    "prompt": prompt,
                    "reference_images": [face_image_url],
                    "num_images": num_images,
                    "guidance_scale": 1.2,
                    "num_inference_steps": 4,
                    "id_weight": 1.0,
                }
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            return {
                "images": [img["url"] for img in result.get("images", [])],
                "generation_time_ms": generation_time_ms,
            }
        except Exception as e:
            print(f"[WARNING] PuLID face reference failed: {e}, falling back to regular FLUX")
            # Fall back to regular FLUX generation
            return await self.generate_thumbnail(
                prompt=prompt,
                num_images=num_images,
                image_size=image_size,
            )

    async def inpaint(
        self,
        image_url: str,
        mask_url: str,
        prompt: str,
        lora_url: Optional[str] = None,
    ) -> dict:
        """
        Inpaint a region of an image.

        Used for editing text or elements in generated thumbnails.

        Args:
            image_url: Original image URL
            mask_url: Mask image URL (white = area to edit)
            prompt: What to generate in the masked area
            lora_url: Optional LoRA for face consistency

        Returns:
            Dictionary with edited image URL
        """
        start_time = time.time()

        arguments = {
            "image_url": image_url,
            "mask_url": mask_url,
            "prompt": prompt,
        }

        if lora_url:
            arguments["loras"] = [{"path": lora_url, "scale": 0.8}]

        result = await fal_client.run_async(
            "fal-ai/flux-pro/v1/fill",
            arguments=arguments
        )

        generation_time_ms = int((time.time() - start_time) * 1000)

        return {
            "image_url": result["images"][0]["url"],
            "generation_time_ms": generation_time_ms,
        }

    async def upscale(
        self,
        image_url: str,
        scale: int = 2,
    ) -> dict:
        """
        Upscale an image for higher resolution output.

        Args:
            image_url: Image to upscale
            scale: Upscale factor (2 or 4)

        Returns:
            Dictionary with upscaled image URL
        """
        result = await fal_client.run_async(
            "fal-ai/clarity-upscaler",
            arguments={
                "image_url": image_url,
                "scale": scale,
            }
        )

        return {
            "image_url": result["image"]["url"],
        }
