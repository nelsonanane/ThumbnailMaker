"""
Text Overlay Service
Adds professional text overlays to thumbnail images using Pillow.
"""
import base64
import io
import os
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class TextOverlayService:
    """Adds professional text overlays to thumbnail images."""

    # Font presets for different thumbnail styles
    FONT_PRESETS = {
        "impact": {
            "family": "Impact",
            "fallbacks": ["Arial Black", "Helvetica Bold", "DejaVuSans-Bold"],
            "weight": "bold",
        },
        "modern": {
            "family": "Montserrat",
            "fallbacks": ["Arial", "Helvetica", "DejaVuSans"],
            "weight": "bold",
        },
        "dramatic": {
            "family": "Bebas Neue",
            "fallbacks": ["Impact", "Arial Black", "DejaVuSans-Bold"],
            "weight": "regular",
        },
        "clean": {
            "family": "Roboto",
            "fallbacks": ["Arial", "Helvetica", "DejaVuSans"],
            "weight": "bold",
        },
    }

    # Color presets for text
    COLOR_PRESETS = {
        "white_shadow": {
            "fill": "#FFFFFF",
            "stroke": "#000000",
            "shadow": "#000000",
        },
        "yellow_pop": {
            "fill": "#FFFF00",
            "stroke": "#000000",
            "shadow": "#000000",
        },
        "red_alert": {
            "fill": "#FF0000",
            "stroke": "#FFFFFF",
            "shadow": "#000000",
        },
        "blue_trust": {
            "fill": "#00BFFF",
            "stroke": "#000000",
            "shadow": "#000000",
        },
        "green_success": {
            "fill": "#00FF00",
            "stroke": "#000000",
            "shadow": "#000000",
        },
    }

    # Position presets
    POSITION_PRESETS = {
        "top_left": (0.05, 0.1),
        "top_center": (0.5, 0.1),
        "top_right": (0.95, 0.1),
        "center": (0.5, 0.5),
        "bottom_left": (0.05, 0.85),
        "bottom_center": (0.5, 0.85),
        "bottom_right": (0.95, 0.85),
    }

    def __init__(self, fonts_dir: Optional[str] = None):
        """
        Initialize the text overlay service.

        Args:
            fonts_dir: Directory containing custom fonts (optional)
        """
        self.fonts_dir = fonts_dir or os.path.join(
            os.path.dirname(__file__), "..", "assets", "fonts"
        )
        self._font_cache = {}

    def _get_font(self, preset: str, size: int) -> ImageFont.FreeTypeFont:
        """Get a font with fallback support."""
        cache_key = f"{preset}_{size}"
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        font_config = self.FONT_PRESETS.get(preset, self.FONT_PRESETS["impact"])
        font_names = [font_config["family"]] + font_config["fallbacks"]

        font = None
        for font_name in font_names:
            # Try custom fonts directory first
            if self.fonts_dir:
                for ext in [".ttf", ".otf"]:
                    font_path = os.path.join(self.fonts_dir, f"{font_name}{ext}")
                    if os.path.exists(font_path):
                        try:
                            font = ImageFont.truetype(font_path, size)
                            break
                        except Exception:
                            continue

            # Try system fonts
            if font is None:
                try:
                    font = ImageFont.truetype(font_name, size)
                    break
                except Exception:
                    continue

        # Fallback to default
        if font is None:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
            except Exception:
                font = ImageFont.load_default()

        self._font_cache[cache_key] = font
        return font

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def add_text(
        self,
        image_data: str,
        text: str,
        position: str = "bottom_center",
        font_preset: str = "impact",
        color_preset: str = "white_shadow",
        font_size: Optional[int] = None,
        stroke_width: int = 4,
        shadow_offset: int = 5,
        max_width_ratio: float = 0.9,
        custom_position: Optional[Tuple[float, float]] = None,
        custom_colors: Optional[dict] = None,
    ) -> str:
        """
        Add text overlay to an image.

        Args:
            image_data: Base64 encoded image or data URI
            text: Text to add
            position: Position preset name
            font_preset: Font style preset
            color_preset: Color scheme preset
            font_size: Override font size (auto-calculated if None)
            stroke_width: Stroke/outline width in pixels
            shadow_offset: Drop shadow offset in pixels
            max_width_ratio: Max text width as ratio of image width
            custom_position: Custom (x_ratio, y_ratio) position
            custom_colors: Custom color dict with fill, stroke, shadow

        Returns:
            Base64 encoded image with text overlay
        """
        # Decode the image
        if image_data.startswith("data:"):
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        width, height = image.size

        # Create overlay for text
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Calculate font size if not specified
        if font_size is None:
            # Dynamic sizing based on text length and image size
            base_size = int(height * 0.12)  # 12% of height as base
            # Reduce size for longer text
            if len(text) > 20:
                base_size = int(base_size * 0.8)
            if len(text) > 30:
                base_size = int(base_size * 0.7)
            font_size = max(base_size, 24)

        font = self._get_font(font_preset, font_size)

        # Get colors
        colors = custom_colors or self.COLOR_PRESETS.get(
            color_preset, self.COLOR_PRESETS["white_shadow"]
        )
        fill_color = self._hex_to_rgb(colors["fill"])
        stroke_color = self._hex_to_rgb(colors["stroke"])
        shadow_color = self._hex_to_rgb(colors["shadow"]) + (128,)  # Semi-transparent shadow

        # Get position
        pos_ratios = custom_position or self.POSITION_PRESETS.get(
            position, self.POSITION_PRESETS["bottom_center"]
        )

        # Calculate text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Wrap text if too wide
        max_width = int(width * max_width_ratio)
        if text_width > max_width:
            text = self._wrap_text(text, font, max_width, draw)
            bbox = draw.multiline_textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

        # Calculate actual position
        x = int(width * pos_ratios[0] - text_width / 2)
        y = int(height * pos_ratios[1] - text_height / 2)

        # Clamp position to stay within bounds
        x = max(10, min(x, width - text_width - 10))
        y = max(10, min(y, height - text_height - 10))

        # Draw shadow
        if shadow_offset > 0:
            shadow_pos = (x + shadow_offset, y + shadow_offset)
            if "\n" in text:
                draw.multiline_text(
                    shadow_pos, text, font=font, fill=shadow_color, align="center"
                )
            else:
                draw.text(shadow_pos, text, font=font, fill=shadow_color)

        # Draw stroke/outline
        if stroke_width > 0:
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx * dx + dy * dy <= stroke_width * stroke_width:
                        stroke_pos = (x + dx, y + dy)
                        if "\n" in text:
                            draw.multiline_text(
                                stroke_pos, text, font=font, fill=stroke_color, align="center"
                            )
                        else:
                            draw.text(stroke_pos, text, font=font, fill=stroke_color)

        # Draw main text
        if "\n" in text:
            draw.multiline_text((x, y), text, font=font, fill=fill_color, align="center")
        else:
            draw.text((x, y), text, font=font, fill=fill_color)

        # Composite overlay onto image
        result = Image.alpha_composite(image, overlay)
        result = result.convert("RGB")

        # Encode back to base64
        buffer = io.BytesIO()
        result.save(buffer, format="PNG", quality=95)
        buffer.seek(0)

        return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode('utf-8')}"

    def _wrap_text(
        self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw
    ) -> str:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def add_multiple_texts(
        self,
        image_data: str,
        texts: List[dict],
    ) -> str:
        """
        Add multiple text overlays to an image.

        Args:
            image_data: Base64 encoded image or data URI
            texts: List of text config dicts, each containing:
                - text: The text string
                - position: Position preset or custom tuple
                - font_preset: Font style
                - color_preset: Color scheme
                - font_size: Optional size override

        Returns:
            Base64 encoded image with all text overlays
        """
        result = image_data

        for text_config in texts:
            result = self.add_text(
                image_data=result,
                text=text_config.get("text", ""),
                position=text_config.get("position", "bottom_center"),
                font_preset=text_config.get("font_preset", "impact"),
                color_preset=text_config.get("color_preset", "white_shadow"),
                font_size=text_config.get("font_size"),
                custom_position=text_config.get("custom_position"),
                custom_colors=text_config.get("custom_colors"),
            )

        return result

    def add_gradient_background(
        self,
        image_data: str,
        position: str = "bottom",
        opacity: float = 0.6,
        height_ratio: float = 0.3,
    ) -> str:
        """
        Add a gradient background for better text readability.

        Args:
            image_data: Base64 encoded image
            position: "top" or "bottom"
            opacity: Gradient max opacity (0-1)
            height_ratio: Height of gradient as ratio of image height

        Returns:
            Image with gradient overlay
        """
        if image_data.startswith("data:"):
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        width, height = image.size

        # Create gradient overlay
        gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gradient_height = int(height * height_ratio)

        for y in range(gradient_height):
            if position == "bottom":
                actual_y = height - gradient_height + y
                alpha = int(255 * opacity * (y / gradient_height))
            else:  # top
                actual_y = y
                alpha = int(255 * opacity * (1 - y / gradient_height))

            for x in range(width):
                gradient.putpixel((x, actual_y), (0, 0, 0, alpha))

        result = Image.alpha_composite(image, gradient)
        result = result.convert("RGB")

        buffer = io.BytesIO()
        result.save(buffer, format="PNG", quality=95)
        buffer.seek(0)

        return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode('utf-8')}"
