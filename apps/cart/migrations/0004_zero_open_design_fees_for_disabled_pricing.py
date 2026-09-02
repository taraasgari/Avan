from django.db import migrations


def zero_open_cart_design_fees(apps, schema_editor):
    MarketplaceSettings = apps.get_model("marketplace", "MarketplaceSettings")
    CartItem = apps.get_model("cart", "CartItem")
    Cart = apps.get_model("cart", "Cart")

    config = MarketplaceSettings.objects.filter(pk=1).first()
    pricing_enabled = bool(config and config.creator_pricing_enabled)
    if not pricing_enabled:
        CartItem.objects.filter(cart__status="open").update(design_fee=0)


class Migration(migrations.Migration):
    dependencies = [
        ("cart", "0003_creator_design_fee"),
        ("marketplace", "0002_marketplacesettings_creator_pricing_enabled"),
    ]

    operations = [
        migrations.RunPython(zero_open_cart_design_fees, migrations.RunPython.noop),
    ]
