"""
LoRA Trainer Service
Trains face models using fal.ai FLUX LoRA training.
"""
import os
from typing import Optional, Callable
import fal_client
from supabase import create_client, Client


class LoRATrainer:
    """Trains custom LoRA models for face consistency."""

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize the LoRA trainer.

        Args:
            supabase_url: Supabase project URL (or from env)
            supabase_key: Supabase service key (or from env)
        """
        url = supabase_url or os.environ.get("SUPABASE_URL")
        key = supabase_key or os.environ.get("SUPABASE_SERVICE_KEY")

        if url and key:
            self.supabase: Client = create_client(url, key)
        else:
            self.supabase = None

    def _generate_trigger_word(self, user_id: str) -> str:
        """Generate a unique trigger word for the user's face model."""
        # Use first 8 chars of user_id to create unique trigger
        short_id = user_id.replace("-", "")[:8].upper()
        return f"FACE_{short_id}"

    async def start_training(
        self,
        user_id: str,
        images_zip_url: str,
        model_name: str,
        on_progress: Optional[Callable] = None,
    ) -> dict:
        """
        Start LoRA training for a face model.

        Args:
            user_id: User's ID
            images_zip_url: URL to ZIP file containing training images
            model_name: User-provided name for the model
            on_progress: Optional callback for progress updates

        Returns:
            Dictionary with model_id, trigger_word, lora_url, status
        """
        trigger_word = self._generate_trigger_word(user_id)

        # Create database record
        model_id = None
        if self.supabase:
            record = self.supabase.table("face_models").insert({
                "user_id": user_id,
                "name": model_name,
                "trigger_word": trigger_word,
                "lora_url": None,
                "training_status": "training"
            }).execute()
            model_id = record.data[0]["id"]

        try:
            # Progress callback wrapper
            def handle_update(update):
                if on_progress and hasattr(update, 'logs'):
                    for log in update.logs:
                        on_progress(log.get("message", ""))

            # Start fal.ai training
            result = await fal_client.subscribe_async(
                "fal-ai/flux-lora-portrait-trainer",
                arguments={
                    "images_data_url": images_zip_url,
                    "trigger_word": trigger_word,
                    "steps": 1000,  # Good balance of quality/time
                    "is_style": False,  # We're training faces, not styles
                    "face_crop_enabled": True,  # Auto-detect and crop faces
                    "create_masks": True,  # Better focus on faces
                },
                with_logs=True,
                on_queue_update=handle_update,
            )

            lora_url = result["diffusers_lora_file"]["url"]

            # Update database with success
            if self.supabase and model_id:
                self.supabase.table("face_models").update({
                    "lora_url": lora_url,
                    "training_status": "completed"
                }).eq("id", model_id).execute()

            return {
                "model_id": model_id,
                "trigger_word": trigger_word,
                "lora_url": lora_url,
                "status": "completed",
            }

        except Exception as e:
            # Update database with failure
            if self.supabase and model_id:
                self.supabase.table("face_models").update({
                    "training_status": "failed",
                    "error_message": str(e),
                }).eq("id", model_id).execute()

            raise

    async def get_training_status(self, model_id: str) -> dict:
        """
        Get the status of a training job.

        Args:
            model_id: Face model ID

        Returns:
            Dictionary with status and model details
        """
        if not self.supabase:
            raise ValueError("Supabase not configured")

        result = self.supabase.table("face_models").select("*").eq("id", model_id).single().execute()

        if not result.data:
            raise ValueError(f"Model not found: {model_id}")

        return result.data

    async def list_user_models(self, user_id: str) -> list:
        """
        List all face models for a user.

        Args:
            user_id: User's ID

        Returns:
            List of face model dictionaries
        """
        if not self.supabase:
            return []

        result = self.supabase.table("face_models").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

        return result.data

    async def delete_model(self, model_id: str, user_id: str) -> bool:
        """
        Delete a face model.

        Args:
            model_id: Face model ID
            user_id: User's ID (for authorization)

        Returns:
            True if deleted successfully
        """
        if not self.supabase:
            raise ValueError("Supabase not configured")

        # Verify ownership
        result = self.supabase.table("face_models").select("user_id").eq("id", model_id).single().execute()

        if not result.data or result.data["user_id"] != user_id:
            raise ValueError("Model not found or unauthorized")

        self.supabase.table("face_models").delete().eq("id", model_id).execute()

        return True
