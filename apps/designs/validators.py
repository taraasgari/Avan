from rest_framework import serializers


MAX_LAYERS_PER_SIDE = 40
ALLOWED_LAYER_TYPES = {"text", "image", "sticker", "ai"}
ALLOWED_SIDES = ("front", "back", "left_sleeve", "right_sleeve", "neck_label")
ALLOWED_GARMENT_TYPES = {"tee", "hoodie", "crop"}
STAGE_COORDINATE_SPACE = "garment-stage-v2"
LEGACY_COORDINATE_SPACE = "print-zone-v1"


def _number(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _integer(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _boolean(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _clean_layer(layer):
    if not isinstance(layer, dict):
        raise serializers.ValidationError("Invalid layer.")

    layer_type = layer.get("type")
    if layer_type not in ALLOWED_LAYER_TYPES:
        raise serializers.ValidationError("Unsupported layer type.")

    # Stage 20 intentionally allows a small amount of canvas bleed.  The previous
    # validator clamped this to 0..100, so an element moved partly outside the
    # garment jumped after save/reload.
    clean = {
        "id": str(layer.get("id", ""))[:80],
        "type": layer_type,
        "x": max(-20, min(120, _number(layer.get("x"), 50))),
        "y": max(-20, min(120, _number(layer.get("y"), 50))),
        "width": max(3, min(180, _number(layer.get("width"), 35))),
        "rotation": max(-180, min(180, _number(layer.get("rotation"), 0))),
        "opacity": max(0, min(1, _number(layer.get("opacity"), 1))),
        "z": _integer(layer.get("z"), 0),
        "flipX": _boolean(layer.get("flipX", False)),
        "flipY": _boolean(layer.get("flipY", False)),
        "hidden": _boolean(layer.get("hidden", False)),
        "locked": _boolean(layer.get("locked", False)),
    }

    if layer_type == "text":
        # Stage 20 uses size/weight.  Accept the older fontSize/fontWeight aliases
        # so saved designs from the previous studio are migrated without losing
        # typography.
        size = layer.get("size", layer.get("fontSize", 48))
        weight = layer.get("weight", layer.get("fontWeight", 700))
        clean.update({
            "text": str(layer.get("text", "YOUR TEXT"))[:240],
            "size": max(4, min(160, _number(size, 48))),
            "color": str(layer.get("color", "#111111"))[:24],
            "weight": max(100, min(900, _integer(weight, 700))),
            "fontFamily": str(layer.get("fontFamily", "Tahoma, Arial, sans-serif"))[:180],
            "fontId": str(layer.get("fontId", ""))[:32],
            "align": str(layer.get("align", "center"))[:10],
            "letterSpacing": max(-4, min(24, _number(layer.get("letterSpacing"), 0))),
            "lineHeight": max(0.7, min(2.2, _number(layer.get("lineHeight"), 1.05))),
            # Preserve legacy effects even though the current Stage 20 sidebar
            # does not expose them yet.
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
            "coordinateSpace": STAGE_COORDINATE_SPACE,
            "garment": {"fabric": "cotton", "garmentType": "tee", "colorHex": ""},
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

    try:
        incoming_version = int(value.get("version", 2) or 2)
    except (TypeError, ValueError):
        incoming_version = 2

    coordinate_space = str(value.get("coordinateSpace") or "").strip()
    if coordinate_space not in {STAGE_COORDINATE_SPACE, LEGACY_COORDINATE_SPACE}:
        # Version-1 documents were print-zone relative.  Version-2 documents
        # without a marker include the Stage 20 saves affected by the old
        # validator, so treat them as stage coordinates to stop repeated
        # migrations on every reload.
        coordinate_space = LEGACY_COORDINATE_SPACE if incoming_version < 2 else STAGE_COORDINATE_SPACE

    normalized = {
        "version": 2,
        "coordinateSpace": coordinate_space,
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
