import csv
import io
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import Category, Color, Product, ProductVariant, Size


CSV_FIELDS = [
    "sku", "product_slug", "name_en", "name_fa", "category_slug", "category_en", "category_fa",
    "description_en", "description_fa", "base_price", "product_type", "color_slug", "color_name",
    "color_hex", "size", "stock", "active", "featured",
]


def _bool(value, default=True):
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _int(value, field, minimum=0):
    try:
        number = int(str(value or "0").strip())
    except ValueError as exc:
        raise ValidationError(f"{field} must be an integer.") from exc
    if number < minimum:
        raise ValidationError(f"{field} must be at least {minimum}.")
    return number


def _money(value, field):
    try:
        number = Decimal(str(value or "0").replace(",", "").strip())
    except InvalidOperation as exc:
        raise ValidationError(f"{field} is not a valid amount.") from exc
    if number < 0:
        raise ValidationError(f"{field} cannot be negative.")
    return number.quantize(Decimal("1"))


def _read_rows(uploaded_file):
    raw = uploaded_file.read()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8-sig")
    else:
        text = raw
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValidationError("CSV has no header row.")
    missing = [field for field in ["sku", "product_slug", "category_slug", "base_price", "color_slug", "size", "stock"] if field not in reader.fieldnames]
    if missing:
        raise ValidationError("Missing columns: " + ", ".join(missing))
    return list(reader)


def _validate_row(row, number):
    cleaned = {key: (row.get(key) or "").strip() for key in CSV_FIELDS}
    if not cleaned["sku"]:
        raise ValidationError("sku is required.")
    if not cleaned["product_slug"]:
        raise ValidationError("product_slug is required.")
    if not cleaned["category_slug"]:
        raise ValidationError("category_slug is required.")
    if not cleaned["color_slug"]:
        raise ValidationError("color_slug is required.")
    if not cleaned["size"]:
        raise ValidationError("size is required.")
    cleaned["base_price"] = _money(cleaned["base_price"], "base_price")
    cleaned["stock"] = _int(cleaned["stock"], "stock")
    if cleaned["product_type"] not in {"", Product.ProductType.READY, Product.ProductType.CUSTOMIZABLE}:
        raise ValidationError("product_type must be ready or customizable.")
    if cleaned["color_hex"] and (not cleaned["color_hex"].startswith("#") or len(cleaned["color_hex"]) != 7):
        raise ValidationError("color_hex must look like #111111.")
    cleaned["active"] = _bool(cleaned["active"], True)
    cleaned["featured"] = _bool(cleaned["featured"], False)
    return cleaned


def import_catalog_csv(uploaded_file, actor=None, apply=False):
    rows = _read_rows(uploaded_file)
    errors = []
    valid_rows = []
    for index, row in enumerate(rows, start=2):
        try:
            valid_rows.append((index, _validate_row(row, index)))
        except ValidationError as exc:
            errors.append({"row": index, "error": "; ".join(exc.messages)})

    if errors or not apply:
        return {"total": len(rows), "success": len(valid_rows), "errors": errors, "applied": False}

    with transaction.atomic():
        for row_number, data in valid_rows:
            category, _ = Category.objects.get_or_create(
                slug=data["category_slug"],
                defaults={
                    "name": data["category_en"] or data["category_fa"] or data["category_slug"],
                    "name_en": data["category_en"],
                    "name_fa": data["category_fa"],
                },
            )
            changed = []
            if data["category_en"] and category.name_en != data["category_en"]:
                category.name_en = data["category_en"]; changed.append("name_en")
            if data["category_fa"] and category.name_fa != data["category_fa"]:
                category.name_fa = data["category_fa"]; changed.append("name_fa")
            if changed:
                category.save(update_fields=changed)

            product, _ = Product.objects.get_or_create(
                slug=data["product_slug"],
                defaults={
                    "name": data["name_en"] or data["name_fa"] or data["product_slug"],
                    "name_en": data["name_en"],
                    "name_fa": data["name_fa"],
                    "description_en": data["description_en"],
                    "description_fa": data["description_fa"],
                    "category": category,
                    "base_price": data["base_price"],
                    "product_type": data["product_type"] or Product.ProductType.READY,
                    "is_active": data["active"],
                    "is_featured": data["featured"],
                },
            )
            product.category = category
            product.base_price = data["base_price"]
            product.product_type = data["product_type"] or product.product_type
            product.is_active = data["active"]
            product.is_featured = data["featured"]
            if data["name_en"]: product.name_en = data["name_en"]
            if data["name_fa"]: product.name_fa = data["name_fa"]
            if data["description_en"]: product.description_en = data["description_en"]
            if data["description_fa"]: product.description_fa = data["description_fa"]
            if not product.name:
                product.name = product.name_en or product.name_fa or product.slug
            product.full_clean()
            product.save()

            color, _ = Color.objects.get_or_create(
                slug=data["color_slug"],
                defaults={"name": data["color_name"] or data["color_slug"], "hex_code": data["color_hex"]},
            )
            if data["color_name"]: color.name = data["color_name"]
            if data["color_hex"]: color.hex_code = data["color_hex"].upper()
            color.full_clean(); color.save()

            size, _ = Size.objects.get_or_create(name=data["size"])
            variant, _ = ProductVariant.objects.get_or_create(
                product=product,
                color=color,
                size=size,
                defaults={"sku": data["sku"], "stock": data["stock"], "is_active": data["active"]},
            )
            if variant.sku != data["sku"]:
                variant.sku = data["sku"]
            variant.stock = data["stock"]
            variant.is_active = data["active"]
            variant.full_clean(); variant.save()

    return {"total": len(rows), "success": len(valid_rows), "errors": [], "applied": True}


def catalog_csv_rows():
    variants = ProductVariant.objects.select_related("product", "product__category", "color", "size").order_by("product__slug", "sku")
    for variant in variants:
        product = variant.product
        category = product.category
        yield {
            "sku": variant.sku,
            "product_slug": product.slug,
            "name_en": product.name_en,
            "name_fa": product.name_fa,
            "category_slug": category.slug,
            "category_en": category.name_en,
            "category_fa": category.name_fa,
            "description_en": product.description_en,
            "description_fa": product.description_fa,
            "base_price": str(product.base_price),
            "product_type": product.product_type,
            "color_slug": variant.color.slug,
            "color_name": variant.color.name,
            "color_hex": variant.color.hex_code,
            "size": variant.size.name,
            "stock": str(variant.stock),
            "active": "1" if variant.is_active and product.is_active else "0",
            "featured": "1" if product.is_featured else "0",
        }
