"""
Prompt Generator Service
Uses LLM to generate image prompts from video content.
"""
import json
from typing import Optional
import openai


# System prompt for the LLM
SYSTEM_PROMPT = """You are a YouTube Thumbnail Architect specializing in viral, high-CTR thumbnail designs.

Your task: Analyze the video content and generate a detailed image prompt for FLUX AI image generation.

RULES:
1. SUBJECT: If a person should appear, use the token "{trigger_word}" to represent them. Describe their expression vividly (shocked with mouth wide open, excited with eyes sparkling, skeptical with raised eyebrow, pointing dramatically).

2. COMPOSITION: Use proven viral layouts:
   - Split screen: face on right, dramatic object/scene on left
   - Close-up: face filling 60% of frame with text beside it
   - Before/After: contrasting elements on each side
   - Centered: single dramatic focal point

3. TEXT: Include SHORT punchy text (2-4 words max) that creates curiosity or urgency. Put text in single quotes within the prompt. Text should be:
   - All caps or title case
   - High contrast against background
   - Positioned where it won't overlap the face

4. LIGHTING: Always specify dramatic lighting:
   - Rim light / edge light for subject separation
   - Volumetric lighting / god rays for drama
   - Studio softbox for clean professional look
   - Colored accent lights (blue, orange, red) for mood

5. STYLE: Include quality tokens:
   - "4k resolution" or "8k"
   - "hyper-realistic" or "photorealistic"
   - "sharp focus"
   - "vibrant saturated colors"
   - "professional photography"

6. BACKGROUND: Describe a relevant, slightly blurred background that adds context without distracting.

{reference_style_section}

OUTPUT FORMAT:
Return ONLY a valid JSON object with these exact fields:
{{
    "prompt": "The complete FLUX image generation prompt (detailed, 50-100 words)",
    "thumbnail_text": "The 2-4 word text that should appear on the thumbnail",
    "emotion": "The primary emotion the thumbnail should convey (one word)",
    "composition": "Brief description of the layout (10 words max)"
}}

Do not include any explanation or text outside the JSON object."""


REFERENCE_STYLE_SECTION = """
7. REFERENCE IMAGE REPLICATION:
   The user has provided a reference thumbnail. You MUST replicate its EXACT structure:

   COMPOSITION:
   {composition_details}

   PERSON PLACEMENT:
   {person_details}

   TEXT ELEMENTS (adapt text to video topic but keep same styling):
   {text_details}

   GRAPHIC ELEMENTS:
   {graphic_details}

   COLORS:
   {color_details}

   MOOD: {mood}

   RECREATION TEMPLATE:
   {recreation_prompt}

   CRITICAL: Replicate the EXACT layout, composition, and style of the reference. Only change:
   1. The person (use the face description provided)
   2. The text content (adapt to the video topic)
   3. The screen/graphic content (adapt to video topic)

   Keep EVERYTHING ELSE identical: colors, positions, lighting style, composition percentages."""


class PromptGenerator:
    """Generates image prompts from video analysis using LLM."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the prompt generator.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o)
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate_prompt(
        self,
        video_data: dict,
        template_system_prompt: Optional[str] = None,
        trigger_word: str = "person",
        reference_analysis: Optional[dict] = None,
        face_description: Optional[str] = None,
    ) -> dict:
        """
        Generate a thumbnail prompt from video analysis.

        Args:
            video_data: Dictionary from VideoAnalyzer.analyze()
            template_system_prompt: Optional template-specific instructions
            trigger_word: Token to use for the person (from LoRA training)
            reference_analysis: Optional analysis from ReferenceAnalyzer
            face_description: Optional description of user's face photos

        Returns:
            Dictionary with prompt, thumbnail_text, emotion, composition
        """
        # Build reference style section if analysis is provided
        reference_style_section = ""
        if reference_analysis:
            # Handle the new detailed JSON structure
            composition = reference_analysis.get('composition', {})
            person = reference_analysis.get('person', {})
            text_elements = reference_analysis.get('text_elements', [])
            graphic_elements = reference_analysis.get('graphic_elements', [])
            colors = reference_analysis.get('colors', {})

            # Format composition details
            composition_details = f"""
   - Layout: {composition.get('layout_type', 'split')}
   - Person position: {composition.get('person_position', 'left 35%')}
   - Person size: {composition.get('person_size', '80% of frame height')}
   - Background zones: {', '.join(composition.get('background_zones', []))}"""

            # Format person details
            person_details = f"""
   - Pose: {person.get('pose', 'facing camera')}
   - Expression: {person.get('expression', 'confident')}
   - Eye direction: {person.get('eye_direction', 'looking at camera')}
   - Lighting: {person.get('lighting_on_face', 'soft front lighting')}"""

            # Format text elements
            text_details = ""
            for i, text in enumerate(text_elements):
                text_details += f"""
   Text {i+1}: "{text.get('text', '')}"
      - Position: {text.get('position', 'top')}
      - Style: {text.get('font_style', 'bold')} {text.get('font_size', 'large')}
      - Color: {text.get('color', 'white')}
      - Effects: {text.get('effects', 'none')}"""

            # Format graphic elements
            graphic_details = ""
            for i, graphic in enumerate(graphic_elements):
                graphic_details += f"""
   Element {i+1}: {graphic.get('type', 'graphic')}
      - Content: {graphic.get('content', '')}
      - Position: {graphic.get('position', '')}
      - Size: {graphic.get('size', 'medium')}"""

            # Format colors
            color_details = f"""
   - Primary: {colors.get('primary', 'white')}
   - Secondary: {colors.get('secondary', 'black')}
   - Accent: {colors.get('accent', 'yellow')}
   - Background: {colors.get('background', 'white')}
   - Text colors: {', '.join(colors.get('text_colors', ['white', 'black']))}"""

            reference_style_section = REFERENCE_STYLE_SECTION.format(
                composition_details=composition_details,
                person_details=person_details,
                text_details=text_details if text_details else "   No text elements",
                graphic_details=graphic_details if graphic_details else "   No graphic elements",
                color_details=color_details,
                mood=reference_analysis.get('mood', 'energetic and professional'),
                recreation_prompt=reference_analysis.get('recreation_prompt', 'Generate a YouTube thumbnail matching the reference style'),
            )

        # Build system prompt
        system = SYSTEM_PROMPT.format(
            trigger_word=trigger_word,
            reference_style_section=reference_style_section
        )

        if template_system_prompt:
            system += f"\n\nADDITIONAL STYLE REQUIREMENTS:\n{template_system_prompt}"

        # Build user content with video analysis
        description = video_data.get('description') or 'No description'
        transcript = video_data.get('transcript') or 'No transcript available'

        # Build face description section
        face_section = ""
        if face_description:
            face_section = f"""

PERSON TO FEATURE IN THUMBNAIL:
{face_description}

IMPORTANT: Replace any person in the reference thumbnail with THIS person described above.
Keep the same pose, expression style, clothing style (or adapt appropriately), and position as the reference.
The person's face and features must match the description above exactly."""

        user_content = f"""Analyze this video and create a viral thumbnail concept:

VIDEO TITLE: {video_data.get('title', 'Unknown')}

VIDEO DESCRIPTION: {description[:500]}

TAGS: {', '.join(video_data.get('tags', [])[:10])}

CHANNEL: {video_data.get('channel', 'Unknown')}

TRANSCRIPT EXCERPT: {transcript[:2000]}

TRIGGER WORD FOR PERSON: {trigger_word}{face_section}

Generate a viral thumbnail concept that will maximize click-through rate."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,  # Some creativity
            max_tokens=500,
        )

        # Parse JSON response with error handling
        raw_content = response.choices[0].message.content
        try:
            # Strip whitespace and parse
            result = json.loads(raw_content.strip())
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', raw_content)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback: create a basic response
                result = {
                    "prompt": f"A YouTube thumbnail for a video about {video_data.get('title', 'content')}, dramatic lighting, 4k, sharp focus",
                    "thumbnail_text": "MUST WATCH",
                    "emotion": "excitement",
                    "composition": "centered dramatic shot"
                }

        # Validate required fields
        required_fields = ["prompt", "thumbnail_text", "emotion", "composition"]
        for field in required_fields:
            if field not in result:
                result[field] = ""

        return result

    def enhance_prompt(
        self,
        base_prompt: str,
        trigger_word: str = "person",
        add_quality_tokens: bool = True
    ) -> str:
        """
        Enhance a user-provided prompt with quality tokens.

        Args:
            base_prompt: User's base prompt
            trigger_word: Token for person
            add_quality_tokens: Whether to add quality enhancement tokens

        Returns:
            Enhanced prompt string
        """
        enhanced = base_prompt

        # Replace generic person references with trigger word
        enhanced = enhanced.replace("a person", f"a {trigger_word}")
        enhanced = enhanced.replace("the person", f"the {trigger_word}")

        if add_quality_tokens:
            quality_tokens = [
                "4k resolution",
                "sharp focus",
                "professional photography",
                "vibrant colors",
            ]

            # Only add tokens not already present
            for token in quality_tokens:
                if token.lower() not in enhanced.lower():
                    enhanced += f", {token}"

        return enhanced
