from rest_framework import serializers


MAX_LAYERS_PER_SIDE = 40
ALLOWED_LAYER_TYPES = {"text", "image", "sticker", "ai"}
ALLOWED_SIDES = {"front", "back", "left_sleeve", "right_sleeve"}
ALLOWED_GARMENT_TYPES = {"tee", "hoodie", "crop"}


def _number(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clean_layer(layer):
    if not isinstance(layer, dict):
        raise serializers.ValidationError("Invalid layer.")

    layer_type = layer.get("type")
    if layer_type not in ALLOWED_LAYER_TYPES:
        raise serializers.ValidationError("Unsupported layer type.")

    clean = {
        "id": str(layer.get("id", ""))[:80],
        "type": layer_type,
        "x": max(0, min(100, _number(layer.get("x"), 50))),
        "y": max(0, min(100, _number(layer.get("y"), 50))),
        "width": max(3, min(120, _number(layer.get("width"), 35))),
        "rotation": max(-180, min(180, _number(layer.get("rotation"), 0))),
        "opacity": max(0.05, min(1, _number(layer.get("opacity"), 1))),
        "z": int(_number(layer.get("z"), 0)),
    }

    if layer_type == "text":
        clean.update({
            "text": str(layer.get("text", "YOUR TEXT"))[:240],
            "fontSize": max(10, min(180, _number(layer.get("fontSize"), 42))),
            "color": str(layer.get("color", "#111111"))[:24],
            "fontWeight": str(layer.get("fontWeight", "800"))[:12],
            "fontFamily": str(layer.get("fontFamily", "Tahoma, Arial, sans-serif"))[:180],
            "fontId": str(layer.get("fontId", ""))[:32],
            "align": str(layer.get("align", "center"))[:10],
            "letterSpacing": max(-8, min(30, _number(layer.get("letterSpacing"), 0))),
            "outline": max(0, min(12, _number(layer.get("outline"), 0))),
            "outlineColor": str(layer.get("outlineColor", "#ffffff"))[:24],
            "shadow": max(0, min(30, _number(layer.get("shadow"), 0))),
        })
    else:
        clean.update({
            "assetId": str(layer.get("assetId", ""))[:80],
            "url": str(layer.get("url", ""))[:700],
            "name": str(layer.get("name", ""))[:120],
        })

    return clean


def validate_design_data(value):
    if value in (None, ""):
        return {
            "version": 2,
            "garment": {"fabric": "cotton", "garmentType": "tee"},
            "sides": {side: [] for side in ALLOWED_SIDES},
        }

    if not isinstance(value, dict):
        raise serializers.ValidationError("Design data must be an object.")

    sides = value.get("sides", {})
    if not isinstance(sides, dict):
        raise serializers.ValidationError("Invalid sides object.")

    garment = value.get("garment", {})
    if garment is None:
        garment = {}
    if not isinstance(garment, dict):
        raise serializers.ValidationError("Invalid garment configuration.")

    garment_type = str(garment.get("garmentType", "tee"))[:16]
    if garment_type not in ALLOWED_GARMENT_TYPES:
        garment_type = "tee"

    normalized = {
        "version": 2,
        "garment": {
            "fabric": str(garment.get("fabric", "cotton"))[:90],
            "garmentType": garment_type,
            "colorHex": str(garment.get("colorHex", ""))[:24],
        },
        "sides": {side: [] for side in ALLOWED_SIDES},
    }

    for side_name, layers in sides.items():
        if side_name not in ALLOWED_SIDES:
            continue
        if not isinstance(layers, list):
            raise serializers.ValidationError(f"{side_name} layers must be a list.")
        if len(layers) > MAX_LAYERS_PER_SIDE:
            raise serializers.ValidationError("Too many design layers.")
        normalized["sides"][side_name] = [_clean_layer(layer) for layer in layers]

    return normalized
