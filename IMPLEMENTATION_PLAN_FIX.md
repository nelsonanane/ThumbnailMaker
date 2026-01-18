# Implementation Plan: Fix Reference Image Handling

## Problem Identified

The reference image is being **passed directly to the image generator (Gemini)**, which causes it to copy the people from the reference instead of just using the format.

**Current broken flow:**
```
Reference Image → Sent to Gemini → Gemini copies people from it ❌
```

**What we want:**
```
Reference Image → Analyze FORMAT only (text) → Text description sent to Gemini ✓
Face Photos → Sent to Gemini → These are the ONLY people ✓
```

## Root Cause (in code)

`backend/services/imagen_generator.py` lines 63-71:
```python
if reference_image:
    ref_bytes = self._decode_base64_image(reference_image)
    content_parts.append(types.Part.from_bytes(data=ref_bytes, mime_type="image/png"))
    content_parts.append("Above is the REFERENCE THUMBNAIL. Replicate its EXACT layout...")
```

This sends the actual reference image to Gemini, which copies the people.

`backend/main.py` lines 312-327:
```python
reference_image = request.reference_thumbnails[0].data  # Getting raw image
result = await imagen_generator.generate_thumbnail(
    reference_image=reference_image,  # Passing to generator ❌
)
```

---

## Correct Implementation

### Concept

1. **Reference Thumbnail** = FORMAT ONLY
   - We already extract format via `reference_analyzer.analyze_reference_thumbnails()`
   - This returns TEXT descriptions of layout, poses, colors, etc.
   - **DO NOT pass the raw image to the generator**

2. **Face Photos** = THE ONLY PEOPLE
   - Pass ALL face photos to the generator
   - These faces REPLACE the character positions in the format
   - Face 1 → Position 1, Face 2 → Position 2, etc.

3. **Video Context** = What the thumbnail is about
   - Title, description, transcript
   - Used to adapt the content (text, graphics) to the topic

---

## Changes Required

### 1. `backend/main.py` - Stop passing reference image to generator

**Before:**
```python
reference_image = request.reference_thumbnails[0].data
result = await imagen_generator.generate_thumbnail(
    reference_image=reference_image,  # ❌ Don't do this
)
```

**After:**
```python
# DO NOT pass reference_image to generator
# The reference_analysis TEXT is already in the prompt
result = await imagen_generator.generate_thumbnail(
    prompt=prompt_data["prompt"],  # Contains format from reference
    face_images=request.face_images,  # ALL face photos
)
```

### 2. `backend/services/imagen_generator.py` - Remove reference_image parameter

**Changes:**
- Remove `reference_image` parameter entirely
- Accept `face_images: List[str]` (all faces, not just one)
- Only add face images to the content, not reference
- Update the prompt to clarify faces replace characters

**New signature:**
```python
async def generate_thumbnail(
    self,
    prompt: str,
    num_images: int = 4,
    face_images: Optional[List[str]] = None,  # ALL faces
    # NO reference_image parameter
) -> dict:
```

**New content building:**
```python
content_parts = []

# Add ALL face photos (these are the ONLY people)
if face_images:
    for i, face_data in enumerate(face_images):
        face_bytes = self._decode_base64_image(face_data)
        if face_bytes:
            content_parts.append(types.Part.from_bytes(data=face_bytes, mime_type="image/png"))
            content_parts.append(f"FACE {i+1}: Use this exact person's face in the thumbnail.")

# Add the main prompt (which contains FORMAT from reference analysis)
content_parts.append(f"""
Generate a YouTube thumbnail.

{prompt}

CRITICAL:
- Use ONLY the faces provided above as the people in the thumbnail
- The format/layout/poses described in the prompt come from a reference (but do NOT include anyone from that reference)
- Apply the described poses and expressions to the provided faces
""")
```

### 3. `backend/services/reference_analyzer.py` - Already correct

The `analyze_reference_thumbnails()` method already extracts FORMAT as text:
- `composition` (layout, positions)
- `pose_format` (expression types, poses)
- `colors`
- `lighting_style`
- `format_prompt`

This is correct - we just need to make sure this TEXT is used, not the raw image.

### 4. `backend/services/prompt_generator.py` - Already correct

Already builds prompt with:
- Video context (title, description, transcript)
- Reference FORMAT (from analysis)
- Face descriptions (from face analysis)

This is correct.

---

## Summary of Changes

| File | Change |
|------|--------|
| `main.py` | Stop passing `reference_image` to generator, pass all `face_images` |
| `imagen_generator.py` | Remove `reference_image` param, accept `face_images` list |
| `reference_analyzer.py` | No changes needed |
| `prompt_generator.py` | No changes needed |

---

## Flow After Fix

```
1. User uploads:
   - Reference thumbnail (for FORMAT)
   - Face photos (the ONLY people)
   - YouTube URL (context)

2. Backend analyzes:
   - reference_analyzer.analyze_reference_thumbnails() → FORMAT as TEXT
   - reference_analyzer.analyze_face_photos() → Face descriptions as TEXT
   - video_analyzer.analyze() → Video context

3. prompt_generator builds prompt:
   - Includes FORMAT text (layout, poses, colors)
   - Includes face descriptions
   - Includes video topic
   - Explicitly says "use ONLY the provided faces"

4. imagen_generator receives:
   - TEXT prompt (containing format + face descriptions + topic)
   - Face IMAGES (the actual photos to use)
   - NO reference image

5. Gemini generates:
   - Uses the layout/poses/colors from the TEXT description
   - Uses the provided face images for the people
   - Does NOT see the reference image, so cannot copy people from it
```

---

## Implementation Order

1. ✅ Create this plan
2. [ ] Update `imagen_generator.py` - remove reference_image, add face_images list
3. [ ] Update `main.py` - stop passing reference_image, pass all face_images
4. [ ] Test locally
5. [ ] Update BUILD_INSTRUCTIONS.md and README.md
6. [ ] Push to GitHub
