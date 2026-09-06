from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.notifications.models import Notification
from apps.growth.security import clear_login_failures, login_blocked, record_login_failure
from apps.orders.models import Order
from apps.wishlist.models import WishlistItem

from .forms import ProfileForm, RegisterForm
from .models import SupportMessage, SupportTicket


User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("accounts:dashboard")

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    error = None
    identifier = ""

    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")

        if login_blocked(request, identifier):
            error = "Too many failed sign-in attempts. Please wait before trying again."
        else:
            user_record = (
                User.objects.filter(
                    Q(username__iexact=identifier) | Q(email__iexact=identifier)
                ).first()
            )

            user = None
            if user_record:
                user = authenticate(
                    request,
                    username=user_record.username,
                    password=password,
                )

            if user is not None:
                clear_login_failures(request, identifier)
                login(request, user)
                next_url = request.GET.get("next")
                if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect("accounts:dashboard")

            record_login_failure(request, identifier)
            error = "Email / username or password is incorrect."

    return render(
        request,
        "accounts/login.html",
        {"error": error, "identifier": identifier},
    )


def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("/")


@login_required(login_url="/account/login/")
def dashboard_view(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")[:6]
    )

    wishlist = (
        WishlistItem.objects.filter(user=request.user)
        .select_related("product", "product__category")
        .prefetch_related("product__images")[:8]
    )

    notifications = request.user.notifications.all()[:5]

    return render(
        request,
        "accounts/dashboard.html",
        {
            "orders": orders,
            "wishlist": wishlist,
            "recent_notifications": notifications,
        },
    )


@login_required(login_url="/account/login/")
def wishlist_page(request):
    wishlist = (
        WishlistItem.objects.filter(user=request.user)
        .select_related("product", "product__category")
        .prefetch_related("product__images")
    )
    return render(request, "accounts/wishlist.html", {"wishlist": wishlist})


@login_required(login_url="/account/login/")
def profile_settings(request):
    saved = False
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        saved = True

    return render(
        request,
        "accounts/profile_settings.html",
        {"form": form, "saved": saved},
    )


@login_required(login_url="/account/login/")
def notification_center(request):
    try:
        from apps.growth.notifications import allowed_notification_kinds
        kinds = allowed_notification_kinds(request.user)
        notifications = request.user.notifications.filter(kind__in=kinds)[:100] if kinds else request.user.notifications.none()
    except Exception:
        notifications = request.user.notifications.all()[:100]
    return render(
        request,
        "accounts/notifications.html",
        {"notifications": notifications},
    )


@login_required(login_url="/account/login/")
@require_POST
def notification_mark_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user,
    )
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    unread = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({"ok": True, "unread": unread})


@login_required(login_url="/account/login/")
@require_POST
def notifications_mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({"ok": True, "unread": 0})

@login_required(login_url="/account/login/")
def support_center(request):
    tickets = request.user.support_tickets.all()[:100]
    return render(request, "accounts/support.html", {"tickets": tickets, "categories": SupportTicket.Category.choices})


@login_required(login_url="/account/login/")
@require_POST
def support_create(request):
    subject = (request.POST.get("subject") or "").strip()[:180]
    body = (request.POST.get("body") or "").strip()[:5000]
    order_number = (request.POST.get("order_number") or "").strip()[:80]
    category = request.POST.get("category") or SupportTicket.Category.OTHER
    valid_categories = {value for value, _ in SupportTicket.Category.choices}
    if category not in valid_categories:
        category = SupportTicket.Category.OTHER
    if len(subject) < 3 or len(body) < 3:
        messages.error(request, "عنوان و متن پیام را کامل وارد کنید.")
        return redirect("accounts:support")

    ticket = SupportTicket.objects.create(
        user=request.user,
        subject=subject,
        category=category,
        order_number=order_number,
        status=SupportTicket.Status.WAITING_SUPPORT,
    )
    SupportMessage.objects.create(ticket=ticket, sender=request.user, body=body, is_staff_reply=False)
    messages.success(request, "درخواست پشتیبانی ثبت شد.")
    return redirect("accounts:support-detail", reference=ticket.reference)


@login_required(login_url="/account/login/")
def support_detail(request, reference):
    ticket = get_object_or_404(SupportTicket.objects.prefetch_related("messages__sender"), reference=reference, user=request.user)
    if request.method == "POST":
        if ticket.status == SupportTicket.Status.CLOSED:
            messages.error(request, "این گفتگو بسته شده است.")
        else:
            body = (request.POST.get("body") or "").strip()[:5000]
            if body:
                SupportMessage.objects.create(ticket=ticket, sender=request.user, body=body, is_staff_reply=False)
                ticket.status = SupportTicket.Status.WAITING_SUPPORT
                ticket.last_message_at = timezone.now()
                ticket.save(update_fields=["status", "last_message_at", "updated_at"])
                messages.success(request, "پیام شما ارسال شد.")
        return redirect("accounts:support-detail", reference=ticket.reference)
    return render(request, "accounts/support_detail.html", {"ticket": ticket})

