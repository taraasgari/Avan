from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.owner.decorators import owner_required

from .forms import ContentReportForm, NotificationPreferenceForm, SeoRedirectForm
from .models import ContentReport, NotificationPreference, SecurityEvent, SeoRedirect


def _owner_context(request, **extra):
    from apps.owner.views import _owner_context as owner_context
    return owner_context(request, **extra)


@login_required(login_url="/account/login/")
def notification_preferences(request):
    preference, _ = NotificationPreference.objects.get_or_create(user=request.user)
    form = NotificationPreferenceForm(request.POST or None, instance=preference)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Notification preferences saved.")
        return redirect("growth:notification-preferences")
    return render(request, "accounts/notification_preferences.html", {"form": form})


@login_required(login_url="/account/login/")
def report_design(request, design_id):
    from apps.designs.models import Design

    design = get_object_or_404(
        Design.objects.select_related("owner"),
        id=design_id,
        status=Design.Status.PUBLISHED,
        visibility=Design.Visibility.PUBLIC,
    )
    if design.owner_id == request.user.id:
        messages.error(request, "You cannot report your own design.")
        return redirect("designs_web:public-design", design_id=design.id)

    duplicate = ContentReport.objects.filter(
        reporter=request.user,
        target_type=ContentReport.TargetType.DESIGN,
        target_id=str(design.id),
        status__in=[ContentReport.Status.OPEN, ContentReport.Status.REVIEWING],
    ).exists()
    form = ContentReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid() and not duplicate:
        item = form.save(commit=False)
        item.reporter = request.user
        item.target_type = ContentReport.TargetType.DESIGN
        item.target_id = str(design.id)
        item.target_label = design.title[:220]
        item.save()
        messages.success(request, "Report submitted for review.")
        return redirect("designs_web:public-design", design_id=design.id)
    return render(request, "growth/report_content.html", {"form": form, "target": design, "duplicate": duplicate, "target_kind": "design"})


@login_required(login_url="/account/login/")
def report_creator(request, username):
    from django.contrib.auth import get_user_model

    creator = get_object_or_404(get_user_model(), username__iexact=username, public_profile_enabled=True)
    if creator.id == request.user.id:
        messages.error(request, "You cannot report your own profile.")
        return redirect("designs_web:creator-profile", username=creator.username)
    duplicate = ContentReport.objects.filter(
        reporter=request.user,
        target_type=ContentReport.TargetType.CREATOR,
        target_id=str(creator.id),
        status__in=[ContentReport.Status.OPEN, ContentReport.Status.REVIEWING],
    ).exists()
    form = ContentReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid() and not duplicate:
        item = form.save(commit=False)
        item.reporter = request.user
        item.target_type = ContentReport.TargetType.CREATOR
        item.target_id = str(creator.id)
        item.target_label = creator.display_name or creator.username
        item.save()
        messages.success(request, "Report submitted for review.")
        return redirect("designs_web:creator-profile", username=creator.username)
    return render(request, "growth/report_content.html", {"form": form, "target": creator, "duplicate": duplicate, "target_kind": "creator"})


def offline_page(request):
    return render(request, "growth/offline.html")


@owner_required
def growth_dashboard(request):
    try:
        from apps.catalog.models import Category, Product
        missing_product_seo = Product.objects.filter(
            Q(seo_title_en="") | Q(seo_description_en="") | Q(seo_title_fa="") | Q(seo_description_fa="")
        ).count()
        missing_category_seo = Category.objects.filter(
            Q(seo_title_en="") | Q(seo_title_fa="")
        ).count()
    except Exception:
        missing_product_seo = missing_category_seo = 0

    return render(request, "owner/growth.html", _owner_context(
        request,
        open_reports=ContentReport.objects.filter(status__in=[ContentReport.Status.OPEN, ContentReport.Status.REVIEWING]).count(),
        security_high_24h=SecurityEvent.objects.filter(severity=SecurityEvent.Severity.HIGH).count(),
        redirects_count=SeoRedirect.objects.filter(is_active=True).count(),
        missing_product_seo=missing_product_seo,
        missing_category_seo=missing_category_seo,
        recent_security=SecurityEvent.objects.all()[:12],
        recent_reports=ContentReport.objects.select_related("reporter")[:8],
    ))


@owner_required
def seo_redirects(request):
    edit_id = request.GET.get("edit")
    instance = get_object_or_404(SeoRedirect, pk=edit_id) if edit_id else None
    form = SeoRedirectForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "SEO redirect saved.")
        return redirect("growth:owner-seo-redirects")
    return render(request, "owner/seo_redirects.html", _owner_context(request, form=form, editing=instance, redirects=SeoRedirect.objects.all()))


@require_POST
@owner_required
def seo_redirect_delete(request, redirect_id):
    get_object_or_404(SeoRedirect, pk=redirect_id).delete()
    messages.success(request, "SEO redirect deleted.")
    return redirect("growth:owner-seo-redirects")


@owner_required
def moderation_queue(request):
    status = request.GET.get("status", "open")
    qs = ContentReport.objects.select_related("reporter", "reviewed_by")
    if status in {choice for choice, _ in ContentReport.Status.choices}:
        qs = qs.filter(status=status)
    return render(request, "owner/moderation.html", _owner_context(request, reports=qs[:200], current_status=status))


@require_POST
@owner_required
def moderation_update(request, report_id):
    report = get_object_or_404(ContentReport, pk=report_id)
    status = request.POST.get("status")
    if status not in {choice for choice, _ in ContentReport.Status.choices}:
        raise Http404
    report.status = status
    report.reviewed_by = request.user
    report.resolution_note = (request.POST.get("resolution_note") or "")[:3000]
    report.save(update_fields=["status", "reviewed_by", "resolution_note", "updated_at"])
    messages.success(request, "Moderation report updated.")
    return redirect("growth:owner-moderation")


@owner_required
def security_center(request):
    kind = request.GET.get("kind", "")
    events = SecurityEvent.objects.select_related("user")
    if kind:
        events = events.filter(kind=kind)
    kinds = list(SecurityEvent.objects.values("kind").annotate(total=Count("id")).order_by("-total")[:20])
    return render(request, "owner/security.html", _owner_context(request, events=events[:250], kinds=kinds, selected_kind=kind))
