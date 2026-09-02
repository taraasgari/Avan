from rest_framework import serializers


MAX_LAYERS_PER_SIDE = 30
ALLOWED_LAYER_TYPES = {"text", "image"}
ALLOWED_SIDES = {"front", "back"}


def validate_design_data(value):
    if value in (None, ""):
        return {"version": 1, "sides": {"front": [], "back": []}}

    if not isinstance(value, dict):
        raise serializers.ValidationError("Design data must be an object.")

    sides = value.get("sides", {})
    if not isinstance(sides, dict):
        raise serializers.ValidationError("Invalid sides object.")

    normalized = {"version": 1, "sides": {"front": [], "back": []}}

    for side_name, layers in sides.items():
        if side_name not in ALLOWED_SIDES:
            continue
        if not isinstance(layers, list):
            raise serializers.ValidationError(f"{side_name} layers must be a list.")
        if len(layers) > MAX_LAYERS_PER_SIDE:
            raise serializers.ValidationError("Too many design layers.")

        clean_layers = []
        for layer in layers:
            if not isinstance(layer, dict):
                raise serializers.ValidationError("Invalid layer.")
            layer_type = layer.get("type")
            if layer_type not in ALLOWED_LAYER_TYPES:
                raise serializers.ValidationError("Unsupported layer type.")

            clean = {
                "id": str(layer.get("id", ""))[:80],
                "type": layer_type,
                "x": max(0, min(100, float(layer.get("x", 50)))),
                "y": max(0, min(100, float(layer.get("y", 50)))),
                "width": max(5, min(100, float(layer.get("width", 35)))),
                "rotation": max(-180, min(180, float(layer.get("rotation", 0)))),
                "z": int(layer.get("z", 0)),
            }

            if layer_type == "text":
                clean.update({
                    "text": str(layer.get("text", "YOUR TEXT"))[:160],
                    "fontSize": max(12, min(120, float(layer.get("fontSize", 38)))),
                    "color": str(layer.get("color", "#111111"))[:20],
                    "fontWeight": str(layer.get("fontWeight", "800"))[:10],
                    "align": str(layer.get("align", "center"))[:10],
                })
            else:
                clean.update({
                    "assetId": str(layer.get("assetId", ""))[:80],
                    "url": str(layer.get("url", ""))[:500],
                })

            clean_layers.append(clean)

        normalized["sides"][side_name] = clean_layers

    return normalized
