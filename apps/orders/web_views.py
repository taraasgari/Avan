from django.shortcuts import render


def checkout_page(request):
    return render(request, "orders/checkout.html")


def order_page(request, number):
    return render(
        request,
        "orders/order_detail.html",
        {
            "order_number": number,
        },
    )