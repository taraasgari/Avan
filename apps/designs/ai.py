import base64
import json
import os
import urllib.error
import urllib.request
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageFilter

from .models import DesignAsset, StudioSettings


OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"


def ai_is_configured():
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def generate_ai_design(*, user, prompt):
    settings = StudioSettings.load()
    if not settings.ai_enabled:
        raise RuntimeError("AI tools are disabled by the site owner.")

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("AI is not configured yet. The owner must set OPENAI_API_KEY on the server.")

    prompt = (prompt or "").strip()
    if len(prompt) < 3:
        raise ValueError("Describe the design you want.")
    prompt = prompt[:1200]

    production_prompt = (
        "Create a single apparel graphic suitable for printing on a fashion T-shirt. "
        "Keep the composition centered, clean, high contrast, no mockup, no person, no garment, "
        "no frame and no watermark. Put only the artwork on a pure white background so the site can "
        "turn it into a cutout sticker. "
        f"User brief: {prompt}"
    )
    body = json.dumps({
        "model": settings.ai_model or "gpt-image-2",
        "prompt": production_prompt,
        "size": "1024x1024",
        "quality": "medium",
        "n": 1,
    }).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_IMAGES_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:600]
        raise RuntimeError(f"AI image generation failed ({exc.code}). {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("The server could not reach the AI image service.") from exc

    data = (payload.get("data") or [{}])[0].get("b64_json")
    if not data:
        raise RuntimeError("AI image service returned no image.")
    try:
        raw = base64.b64decode(data)
    except Exception as exc:
        raise RuntimeError("AI image response could not be decoded.") from exc

    asset = DesignAsset(
        owner=user,
        kind=DesignAsset.Kind.AI,
        original_name="ai-design.png",
        mime_type="image/png",
        source_prompt=prompt,
    )
    asset.image.save("ai-design.png", ContentFile(raw), save=True)
    return asset


def stickerize_asset(*, user, asset):
    if asset.owner_id != user.id:
        raise PermissionError("You can only edit your own design assets.")

    asset.image.open("rb")
    with Image.open(asset.image) as source:
        image = source.convert("RGBA")

    # Turn near-white backgrounds transparent. This is deterministic, local and fast;
    # users can still upload a ready-cut PNG when they need precise subject segmentation.
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            light = min(r, g, b)
            if light >= 248:
                a2 = 0
            elif light >= 220:
                a2 = int(a * (248 - light) / 28)
            else:
                a2 = a
            pixels[x, y] = (r, g, b, a2)

    alpha = image.getchannel("A")
    # A subtle white sticker edge keeps generated graphics readable on dark garments.
    expanded = alpha.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.2))
    outline = Image.new("RGBA", image.size, (255, 255, 255, 0))
    outline.putalpha(expanded)
    outline.alpha_composite(image)

    output = BytesIO()
    outline.save(output, format="PNG", optimize=True)
    output.seek(0)

    new_asset = DesignAsset(
        owner=user,
        kind=DesignAsset.Kind.STICKER,
        original_name=f"sticker-{asset.original_name or 'design'}.png"[:255],
        mime_type="image/png",
        source_prompt=asset.source_prompt,
    )
    new_asset.image.save("sticker.png", ContentFile(output.read()), save=True)
    return new_asset
