"""
Reference Image Analyzer Service
Uses GPT-4o Vision to analyze reference thumbnails and extract style descriptions.
"""
import json
import base64
from typing import List, Optional
import openai


ANALYSIS_SYSTEM_PROMPT = """You are an expert YouTube thumbnail analyst. Your task is to create an EXTREMELY DETAILED structural breakdown of the reference thumbnail that can be used to recreate it with different content.

Analyze EVERY element with precise details:

1. COMPOSITION GRID: Exact layout percentages (e.g., "person occupies left 35%, content right 65%")
2. PERSON DETAILS: Position, pose, expression, clothing, accessories, lighting on face
3. BACKGROUND: Exact description of what's behind the person and in each area
4. TEXT ELEMENTS: Exact text, font style, size relative to image, color, position, effects (shadow, outline, glow)
5. GRAPHIC ELEMENTS: Icons, screenshots, overlays - their exact positions and sizes
6. COLOR VALUES: Specific colors (e.g., "bright yellow #FFD700", "dark navy background")
7. LIGHTING: Direction, intensity, color temperature, any colored lighting effects
8. SPECIAL EFFECTS: Arrows, circles, emojis, badges, borders, gradients

OUTPUT FORMAT:
Return ONLY a valid JSON object with this EXACT structure:
{{
    "composition": {{
        "layout_type": "split/centered/thirds/etc",
        "person_position": "left/right/center with percentage (e.g., 'left 35%')",
        "person_size": "percentage of frame height (e.g., '80%')",
        "background_zones": ["description of each zone from left to right"]
    }},
    "person": {{
        "pose": "exact pose description",
        "expression": "exact facial expression",
        "eye_direction": "looking at camera/looking at content/etc",
        "clothing": "visible clothing and accessories",
        "lighting_on_face": "lighting description"
    }},
    "text_elements": [
        {{
            "text": "exact text content",
            "position": "top/bottom/left/right with specifics",
            "font_style": "bold/italic/etc",
            "font_size": "large/medium/small relative to image",
            "color": "color description or hex",
            "effects": "shadow/outline/glow/none",
            "background": "text background if any"
        }}
    ],
    "graphic_elements": [
        {{
            "type": "screenshot/icon/arrow/emoji/etc",
            "content": "what it shows",
            "position": "where in the frame",
            "size": "relative size"
        }}
    ],
    "colors": {{
        "primary": "main color",
        "secondary": "secondary color",
        "accent": "accent/highlight color",
        "background": "background color(s)",
        "text_colors": ["list of text colors used"]
    }},
    "mood": "overall mood/energy of the thumbnail",
    "recreation_prompt": "A detailed prompt that would recreate this exact thumbnail structure with placeholders for [PERSON_DESCRIPTION] and [VIDEO_TOPIC]"
}}

Be EXTREMELY precise. The goal is to recreate this EXACT layout and style with different content."""


FACE_ANALYSIS_PROMPT = """Analyze this face photo to create a detailed description for AI image generation.

Describe in detail:
1. ETHNICITY/SKIN TONE: Specific description (e.g., "Black man with dark brown skin")
2. FACE SHAPE: Round, oval, square, etc.
3. FACIAL HAIR: Beard, mustache, clean-shaven, stubble
4. HAIR: Style, color, length
5. DISTINCTIVE FEATURES: Any notable features
6. AGE RANGE: Approximate age
7. BUILD: If visible, body type

Return a detailed description that can be inserted into an image generation prompt to accurately represent this person. Format as a single descriptive paragraph that starts with the person's ethnicity and key features.

Example output: "A Black man in his 30s with dark brown skin, short black hair, clean-shaven face, oval face shape, confident expression, athletic build"

Be specific and detailed so the AI can accurately generate images of this person."""


class ReferenceAnalyzer:
    """Analyzes reference thumbnails and face photos using GPT-4o Vision."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the reference analyzer.

        Args:
            api_key: OpenAI API key
            model: Model to use (must support vision)
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def _prepare_image_content(self, image_data: str) -> dict:
        """
        Prepare image data for the OpenAI API.

        Args:
            image_data: Base64 encoded image (with or without data URI prefix)

        Returns:
            Image content dict for OpenAI API
        """
        # Handle data URI format
        if image_data.startswith('data:'):
            # Extract the base64 part
            return {
                "type": "image_url",
                "image_url": {
                    "url": image_data,
                    "detail": "high"
                }
            }
        else:
            # Assume it's raw base64, add data URI prefix
            # Try to detect image type from base64 header
            if image_data.startswith('/9j/'):
                media_type = 'image/jpeg'
            elif image_data.startswith('iVBOR'):
                media_type = 'image/png'
            else:
                media_type = 'image/jpeg'  # Default to JPEG

            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{image_data}",
                    "detail": "high"
                }
            }

    def analyze_reference_thumbnails(
        self,
        reference_images: List[dict],
    ) -> dict:
        """
        Analyze multiple reference thumbnails to extract style information.

        Args:
            reference_images: List of dicts with 'data' (base64) and optional 'description'

        Returns:
            Dictionary with style analysis
        """
        if not reference_images:
            return {
                "style_description": "No reference thumbnails provided",
                "common_elements": [],
                "color_palette": "Default vibrant colors",
                "composition_style": "Standard thumbnail composition",
                "text_style": None,
                "recommendations": "Use standard viral thumbnail practices"
            }

        # Build content array with all images
        content = [
            {
                "type": "text",
                "text": f"Analyze these {len(reference_images)} reference YouTube thumbnails and extract the style information:"
            }
        ]

        for i, ref in enumerate(reference_images):
            # Add the image
            content.append(self._prepare_image_content(ref.get('data', ref) if isinstance(ref, dict) else ref))

            # Add user description if provided
            if isinstance(ref, dict) and ref.get('description'):
                content.append({
                    "type": "text",
                    "text": f"User note for image {i + 1}: {ref['description']}"
                })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,  # Increased for detailed JSON
            temperature=0.2,  # Lower for more precise analysis
        )

        raw_content = response.choices[0].message.content
        print(f"[DEBUG] Reference analysis result: {raw_content[:500]}...")

        try:
            result = json.loads(raw_content.strip())
        except json.JSONDecodeError:
            # Fallback response with new structure
            result = {
                "composition": {
                    "layout_type": "split",
                    "person_position": "left 35%",
                    "person_size": "80%",
                    "background_zones": ["person area", "content area"]
                },
                "person": {
                    "pose": "facing camera",
                    "expression": "engaging",
                    "eye_direction": "looking at camera",
                    "clothing": "casual",
                    "lighting_on_face": "soft front lighting"
                },
                "text_elements": [],
                "graphic_elements": [],
                "colors": {
                    "primary": "white",
                    "secondary": "black",
                    "accent": "yellow",
                    "background": "white",
                    "text_colors": ["black", "yellow"]
                },
                "mood": "energetic and professional",
                "recreation_prompt": "Generate a YouTube thumbnail with person on left, content on right"
            }

        return result

    def analyze_face_photos(
        self,
        face_images: List[str],
    ) -> str:
        """
        Analyze face photos and generate a description for use in thumbnail generation.

        Args:
            face_images: List of base64 encoded face photos

        Returns:
            Combined description of the faces for prompt generation
        """
        if not face_images:
            return ""

        content = [
            {
                "type": "text",
                "text": "Analyze these face photos for use in YouTube thumbnail generation. Describe how to best represent this person in thumbnails:"
            }
        ]

        for face_image in face_images:
            content.append(self._prepare_image_content(face_image))

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": FACE_ANALYSIS_PROMPT},
                {"role": "user", "content": content}
            ],
            max_tokens=300,
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    def generate_style_enhanced_prompt(
        self,
        base_prompt: str,
        reference_analysis: Optional[dict] = None,
        face_description: Optional[str] = None,
    ) -> str:
        """
        Enhance a base prompt with reference style information.

        Args:
            base_prompt: The original image generation prompt
            reference_analysis: Analysis from analyze_reference_thumbnails()
            face_description: Description from analyze_face_photos()

        Returns:
            Enhanced prompt incorporating style information
        """
        enhanced_prompt = base_prompt

        if reference_analysis:
            # Use the recreation_prompt if available (new detailed format)
            if 'recreation_prompt' in reference_analysis:
                recreation = reference_analysis['recreation_prompt']
                # Replace placeholders
                if face_description:
                    recreation = recreation.replace('[PERSON_DESCRIPTION]', face_description)
                recreation = recreation.replace('[VIDEO_TOPIC]', base_prompt)

                enhanced_prompt = recreation

            # Add composition details
            composition = reference_analysis.get('composition', {})
            colors = reference_analysis.get('colors', {})

            style_addition = f"""

EXACT COMPOSITION TO REPLICATE:
- Layout: {composition.get('layout_type', 'split')}
- Person position: {composition.get('person_position', 'left side')}
- Person fills {composition.get('person_size', '80%')} of frame height

EXACT COLORS TO USE:
- Primary: {colors.get('primary', 'white')}
- Accent: {colors.get('accent', 'yellow')}
- Background: {colors.get('background', 'white')}

MOOD: {reference_analysis.get('mood', 'energetic')}
"""
            enhanced_prompt += style_addition

        if face_description:
            enhanced_prompt += f"""

PERSON IN THUMBNAIL (MUST MATCH EXACTLY):
{face_description}
"""

        return enhanced_prompt
