"""
Reference Image Analyzer Service
Uses GPT-4o Vision to analyze reference thumbnails and extract style descriptions.
"""
import json
import base64
from typing import List, Optional
import openai


ANALYSIS_SYSTEM_PROMPT = """You are an expert YouTube thumbnail FORMAT analyst. Your task is to extract the TEMPLATE/FORMAT from a reference thumbnail - NOT the actual people in it.

CRITICAL: The reference image is ONLY for extracting:
- Layout and composition (where things are positioned)
- Expression TYPES and poses (e.g., "shocked expression", "pointing pose") - NOT the actual person
- Color scheme and lighting style
- Text styling and positioning
- Overall mood and energy

DO NOT describe the specific person in the reference. Instead, describe the ROLE and POSE that a person should take.

Analyze these FORMAT elements:

1. COMPOSITION GRID: Exact layout percentages (e.g., "person occupies left 35%, content right 65%")
2. POSE & EXPRESSION FORMAT: The TYPE of pose and expression (e.g., "shocked with mouth open", "pointing at something") - this will be applied to DIFFERENT people
3. BACKGROUND: Description of background elements and zones
4. TEXT ELEMENTS: Text styling, font, size, color, position, effects
5. GRAPHIC ELEMENTS: Icons, screenshots, overlays - positions and sizes
6. COLOR SCHEME: The color palette to use
7. LIGHTING STYLE: Direction, intensity, color temperature
8. NUMBER OF PEOPLE: How many people appear and their positions (e.g., "two people - one on left reacting, one on right")

OUTPUT FORMAT:
Return ONLY a valid JSON object with this EXACT structure:
{{
    "composition": {{
        "layout_type": "split/centered/thirds/etc",
        "person_count": 1,
        "person_positions": ["left 35%", "right 30%"],
        "person_size": "percentage of frame height (e.g., '80%')",
        "background_zones": ["description of each zone from left to right"]
    }},
    "pose_format": {{
        "primary_person": {{
            "position": "left/right/center",
            "pose": "the pose they should strike (e.g., 'leaning forward, pointing')",
            "expression_type": "the expression type (e.g., 'shocked with wide eyes and open mouth')",
            "eye_direction": "looking at camera/looking at content/etc"
        }},
        "secondary_people": [
            {{
                "position": "where this person is",
                "pose": "their pose",
                "expression_type": "their expression type"
            }}
        ]
    }},
    "text_elements": [
        {{
            "text": "exact text content (for reference only - will be changed)",
            "position": "top/bottom/left/right with specifics",
            "font_style": "bold/italic/etc",
            "font_size": "large/medium/small relative to image",
            "color": "color description or hex",
            "effects": "shadow/outline/glow/none"
        }}
    ],
    "graphic_elements": [
        {{
            "type": "screenshot/icon/arrow/emoji/etc",
            "content": "what type of content",
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
    "lighting_style": "description of lighting (e.g., 'dramatic rim lighting from behind')",
    "mood": "overall mood/energy of the thumbnail",
    "format_prompt": "A prompt describing the FORMAT/TEMPLATE only - use [PRIMARY_PERSON] and [SECONDARY_PERSON_N] as placeholders for where the user's faces will go"
}}

REMEMBER: You are extracting a TEMPLATE. The actual people will come from separate face photos provided by the user. Do NOT copy any person's appearance from the reference."""


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


MULTI_FACE_ANALYSIS_PROMPT = """Analyze these face photos. Each photo is a DIFFERENT person who will appear in the thumbnail.

These faces will REPLACE the characters in a reference thumbnail format.

For EACH person, provide a detailed description including:
1. ETHNICITY/SKIN TONE: Specific description
2. FACE SHAPE: Round, oval, square, etc.
3. FACIAL HAIR: Beard, mustache, clean-shaven, stubble
4. HAIR: Style, color, length
5. DISTINCTIVE FEATURES: Any notable features
6. AGE RANGE: Approximate age
7. GENDER: Male/Female

Return a JSON object with this structure:
{
    "faces": [
        {
            "index": 1,
            "description": "Detailed description of person from face photo 1"
        },
        {
            "index": 2,
            "description": "Detailed description of person from face photo 2"
        }
    ],
    "total_faces": 2,
    "combined_description": "A summary describing all people for use in prompts"
}

IMPORTANT:
- Each face photo is a different person
- ALL faces will be used in the final thumbnail
- These faces REPLACE the characters in the reference format (not copy them)
- Be extremely detailed so the AI can accurately generate these specific people"""


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
    ) -> dict:
        """
        Analyze ALL face photos individually and generate descriptions for each.
        All faces are treated equally - they will replace characters in the reference format.

        Args:
            face_images: List of base64 encoded face photos

        Returns:
            Dictionary with individual face descriptions:
            {
                "faces": [
                    {"index": 1, "description": "..."},
                    {"index": 2, "description": "..."}
                ],
                "total_faces": 2,
                "combined_description": "...",
                "face_descriptions": ["desc1", "desc2"]  # Simple list for easy access
            }
        """
        if not face_images:
            return {
                "faces": [],
                "total_faces": 0,
                "combined_description": "",
                "face_descriptions": []
            }

        # Build content with ALL face images labeled
        content = [
            {
                "type": "text",
                "text": f"Analyze these {len(face_images)} face photos. Each is a DIFFERENT person who will appear in the thumbnail:"
            }
        ]

        for i, face_image in enumerate(face_images):
            content.append({
                "type": "text",
                "text": f"\n--- FACE PHOTO {i + 1} ---"
            })
            content.append(self._prepare_image_content(face_image))

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": MULTI_FACE_ANALYSIS_PROMPT},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.3,
        )

        raw_content = response.choices[0].message.content
        print(f"[DEBUG] Face analysis result: {raw_content[:500]}...")

        try:
            result = json.loads(raw_content.strip())
        except json.JSONDecodeError:
            result = {
                "faces": [{"index": 1, "description": "A person"}],
                "combined_description": "A person"
            }

        # Extract face descriptions into a simple list
        faces = result.get("faces", [])
        face_descriptions = [face.get("description", "") for face in faces]

        result["face_descriptions"] = face_descriptions
        result["total_faces"] = len(face_descriptions)

        # Keep backward compatibility (but these are just for legacy code - all faces are equal now)
        result["primary_face"] = face_descriptions[0] if face_descriptions else ""
        result["secondary_faces"] = face_descriptions[1:] if len(face_descriptions) > 1 else []

        return result

    def analyze_single_face(self, face_image: str) -> str:
        """
        Analyze a single face photo (legacy method for backward compatibility).

        Args:
            face_image: Base64 encoded face photo

        Returns:
            Description string for the face
        """
        content = [
            {"type": "text", "text": "Analyze this face photo:"},
            self._prepare_image_content(face_image)
        ]

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
        face_description: Optional[dict] = None,
    ) -> str:
        """
        Enhance a base prompt with reference FORMAT and face descriptions.
        All faces replace characters in the reference format.

        Args:
            base_prompt: The original image generation prompt
            reference_analysis: Analysis from analyze_reference_thumbnails() - FORMAT only
            face_description: Dictionary from analyze_face_photos() with faces list

        Returns:
            Enhanced prompt with format info and ALL faces to use
        """
        enhanced_prompt = base_prompt

        # Get all face descriptions
        face_descriptions = []
        if face_description:
            if isinstance(face_description, dict):
                face_descriptions = face_description.get("face_descriptions", [])
                # Fallback to old format
                if not face_descriptions:
                    if face_description.get("primary_face"):
                        face_descriptions = [face_description.get("primary_face")] + face_description.get("secondary_faces", [])
            else:
                # Legacy string format
                face_descriptions = [face_description]

        if reference_analysis:
            # Use the format_prompt if available
            format_prompt = reference_analysis.get('format_prompt') or reference_analysis.get('recreation_prompt', '')
            if format_prompt:
                # Replace placeholders with face descriptions
                for i, face_desc in enumerate(face_descriptions):
                    format_prompt = format_prompt.replace(f'[FACE_{i+1}]', face_desc)
                    format_prompt = format_prompt.replace(f'[PERSON_{i+1}]', face_desc)
                    # Legacy placeholders
                    if i == 0:
                        format_prompt = format_prompt.replace('[PRIMARY_PERSON]', face_desc)
                        format_prompt = format_prompt.replace('[PERSON_DESCRIPTION]', face_desc)
                    else:
                        format_prompt = format_prompt.replace(f'[SECONDARY_PERSON_{i}]', face_desc)
                format_prompt = format_prompt.replace('[VIDEO_TOPIC]', base_prompt)
                enhanced_prompt = format_prompt

            # Add composition details (FORMAT ONLY)
            composition = reference_analysis.get('composition', {})
            colors = reference_analysis.get('colors', {})
            pose_format = reference_analysis.get('pose_format', {})

            style_addition = f"""

=== REFERENCE FORMAT (layout/style only - NOT the people) ===
Layout: {composition.get('layout_type', 'split')}
Person positions: {composition.get('person_positions', ['left side'])}
Number of characters: {composition.get('person_count', 1)}

Pose/Expression FORMAT to apply:
{pose_format.get('primary_person', {}).get('pose', 'engaging pose')} with {pose_format.get('primary_person', {}).get('expression_type', 'expressive face')}

Colors: {colors.get('primary', 'white')}, {colors.get('accent', 'yellow')}, {colors.get('background', 'white')}
Lighting: {reference_analysis.get('lighting_style', 'dramatic lighting')}
Mood: {reference_analysis.get('mood', 'energetic')}
=== END FORMAT ===
"""
            enhanced_prompt += style_addition

        # Add face descriptions - these REPLACE characters in the reference format
        if face_descriptions:
            enhanced_prompt += f"""

=== FACES TO USE ({len(face_descriptions)} people) ===
These faces REPLACE the characters in the reference format.
DO NOT include anyone from the reference - use ONLY these faces.
"""
            for i, face_desc in enumerate(face_descriptions):
                enhanced_prompt += f"""
FACE {i + 1}:
{face_desc}
"""
            enhanced_prompt += "=== END FACES ==="

        return enhanced_prompt
