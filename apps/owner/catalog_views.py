from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import Category, Color, Product, ProductImage, ProductVariant, Size
from apps.operations.models import ShippingMethod
from apps.operations.services import adjust_stock

from .decorators import owner_required
from .forms_stage9 import CategoryForm, ColorForm, ProductVariantForm, ShippingMethodForm, SizeForm


MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_IMAGE_BATCH = 12


def _base_context(request, **extra):
    # Avoid importing owner.views at module import time; it keeps this module easy to reuse.
    from .views import _owner_context

    return _owner_context(request, **extra)


@owner_required
def catalog_manager(request):
    category_form = CategoryForm(prefix="category")
    color_form = ColorForm(prefix="color")
    size_form = SizeForm(prefix="size")

    if request.method == "POST":
        entity = request.POST.get("entity")
        if entity == "category":
            category_form = CategoryForm(request.POST, prefix="category")
            form = category_form
        elif entity == "color":
            color_form = ColorForm(request.POST, prefix="color")
            form = color_form
        elif entity == "size":
            size_form = SizeForm(request.POST, prefix="size")
            form = size_form
        else:
            return HttpResponseBadRequest("Unknown catalog entity.")

        if form.is_valid():
            form.save()
            messages.success(request, f"{entity.title()} saved.")
            return redirect("owner:catalog-manager")

    return render(
        request,
        "owner/catalog_manager.html",
        _base_context(
            request,
            categories=Category.objects.annotate_product_count().order_by("sort_order", "name")
            if hasattr(Category.objects, "annotate_product_count")
            else Category.objects.order_by("sort_order", "name"),
            colors=Color.objects.order_by("name"),
            sizes=Size.objects.order_by("sort_order", "name"),
            category_form=category_form,
            color_form=color_form,
            size_form=size_form,
        ),
    )


@require_POST
@owner_required
def catalog_delete(request, entity, object_id):
    mapping = {
        "category": Category,
        "color": Color,
        "size": Size,
    }
    model = mapping.get(entity)
    if not model:
        raise Http404
    obj = get_object_or_404(model, pk=object_id)
    try:
        obj.delete()
    except ProtectedError:
        messages.error(request, f"{entity.title()} is in use and cannot be deleted.")
    else:
        messages.success(request, f"{entity.title()} deleted.")
    return redirect("owner:catalog-manager")


@owner_required
def product_media(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == "POST":
        action = request.POST.get("action", "upload")
        if action == "upload":
            files = request.FILES.getlist("images")[:MAX_IMAGE_BATCH]
            if not files:
                messages.error(request, "Choose at least one image.")
                return redirect("owner:product-media", product_id=product.id)

            existing_count = product.images.count()
            uploaded = 0
            for offset, image_file in enumerate(files):
                if image_file.size > MAX_IMAGE_BYTES:
                    messages.error(request, f"{image_file.name}: file is larger than 12 MB.")
                    continue
                item = ProductImage(
                    product=product,
                    image=image_file,
                    alt_text=(request.POST.get("alt_text") or product.name)[:180],
                    sort_order=(existing_count + offset) * 10,
                )
                try:
                    item.full_clean()
                    item.save()
                except ValidationError as exc:
                    messages.error(request, f"{image_file.name}: {exc}")
                    continue
                uploaded += 1
            if uploaded:
                messages.success(request, f"{uploaded} image(s) uploaded.")
            return redirect("owner:product-media", product_id=product.id)

        image = get_object_or_404(ProductImage, pk=request.POST.get("image_id"), product=product)
        if action == "primary":
            with transaction.atomic():
                image.sort_order = -1
                image.save(update_fields=["sort_order"])
                ordered = list(product.images.order_by("sort_order", "id"))
                for index, item in enumerate(ordered):
                    desired = index * 10
                    if item.sort_order != desired:
                        item.sort_order = desired
                        item.save(update_fields=["sort_order"])
            messages.success(request, "Primary product image updated.")
        elif action == "up" or action == "down":
            ordered = list(product.images.order_by("sort_order", "id"))
            position = next((idx for idx, item in enumerate(ordered) if item.pk == image.pk), None)
            if position is not None:
                target = position - 1 if action == "up" else position + 1
                if 0 <= target < len(ordered):
                    ordered[position], ordered[target] = ordered[target], ordered[position]
                    for index, item in enumerate(ordered):
                        item.sort_order = index * 10
                    ProductImage.objects.bulk_update(ordered, ["sort_order"])
        elif action == "delete":
            image.delete()
            messages.success(request, "Image deleted.")
        else:
            return HttpResponseBadRequest("Unknown image action.")
        return redirect("owner:product-media", product_id=product.id)

    return render(
        request,
        "owner/product_media.html",
        _base_context(request, product=product, images=product.images.order_by("sort_order", "id")),
    )


@owner_required
def variant_manager(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    edit_id = request.GET.get("edit")
    instance = get_object_or_404(ProductVariant, pk=edit_id, product=product) if edit_id else None
    form = ProductVariantForm(request.POST or None, instance=instance)

    if request.method == "POST":
        action = request.POST.get("action", "save")
        if action == "delete":
            target = get_object_or_404(ProductVariant, pk=request.POST.get("variant_id"), product=product)
            try:
                target.delete()
            except ProtectedError:
                messages.error(request, "This variant already exists in orders and cannot be deleted. Disable it instead.")
            else:
                messages.success(request, "Variant deleted.")
            return redirect("owner:variant-manager", product_id=product.id)

        if form.is_valid():
            requested_stock = int(form.cleaned_data["stock"])
            try:
                with transaction.atomic():
                    if instance:
                        previous_stock = instance.stock
                        variant = form.save(commit=False)
                        # Stock is adjusted through the inventory service so history stays auditable.
                        variant.stock = previous_stock
                        variant.save()
                        delta = requested_stock - previous_stock
                    else:
                        variant = form.save(commit=False)
                        variant.product = product
                        variant.stock = 0
                        variant.save()
                        delta = requested_stock

                    if delta:
                        adjust_stock(
                            variant_id=variant.id,
                            delta=delta,
                            kind="adjustment",
                            actor=request.user,
                            note="Changed from Owner Product Variant Manager",
                        )
            except (IntegrityError, ValidationError, ValueError) as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Variant saved and inventory history updated.")
                return redirect("owner:variant-manager", product_id=product.id)

    return render(
        request,
        "owner/variant_manager.html",
        _base_context(
            request,
            product=product,
            variants=product.variants.select_related("color", "size").order_by("color__name", "size__sort_order", "size__name"),
            form=form,
            editing=instance,
        ),
    )


@owner_required
def shipping_methods(request):
    edit_id = request.GET.get("edit")
    instance = get_object_or_404(ShippingMethod, pk=edit_id) if edit_id else None
    form = ShippingMethodForm(request.POST or None, instance=instance)

    if request.method == "POST":
        action = request.POST.get("action", "save")
        if action == "delete":
            target = get_object_or_404(ShippingMethod, pk=request.POST.get("method_id"))
            try:
                target.delete()
            except ProtectedError:
                messages.error(request, "This shipping method is referenced by existing shipments. Disable it instead.")
            else:
                messages.success(request, "Shipping method deleted.")
            return redirect("owner:shipping-methods")

        if form.is_valid():
            form.save()
            messages.success(request, "Shipping method saved.")
            return redirect("owner:shipping-methods")

    return render(
        request,
        "owner/shipping_methods.html",
        _base_context(
            request,
            form=form,
            editing=instance,
            methods=ShippingMethod.objects.order_by("sort_order", "id"),
        ),
    )
