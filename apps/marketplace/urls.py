from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("account/creator/wallet/", views.creator_wallet, name="creator-wallet"),
    path("account/creator/wallet/request-payout/", views.request_payout, name="request-payout"),
    path("rewards/redeem/", views.redeem_points, name="redeem-points"),
    path("for-you/", views.for_you, name="for-you"),
]
