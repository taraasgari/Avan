import secrets

from django.db import migrations, models


ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def token(n=8):
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


def fill_codes(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    OrderItem = apps.get_model("orders", "OrderItem")

    for order in Order.objects.filter(tracking_code__isnull=True).iterator():
        code = f"AVN-{str(order.number).replace('-', '')[:6].upper()}-{token(5)}"
        while Order.objects.filter(tracking_code=code).exists():
            code = f"AVN-{str(order.number).replace('-', '')[:6].upper()}-{token(5)}"
        order.tracking_code = code
        order.save(update_fields=["tracking_code"])

    for item in OrderItem.objects.filter(item_tracking_code__isnull=True).iterator():
        code = f"AVN-I-{token(8)}"
        while OrderItem.objects.filter(item_tracking_code=code).exists():
            code = f"AVN-I-{token(8)}"
        item.item_tracking_code = code
        item.save(update_fields=["item_tracking_code"])


class Migration(migrations.Migration):
    dependencies = [("orders", "0004_creator_commerce_snapshot")]

    operations = [
        # Add the fields nullable but already unique. PostgreSQL permits multiple NULL
        # values in a UNIQUE column, so existing rows can be backfilled safely.
        # Doing this avoids Django creating the same varchar pattern-ops index twice
        # when changing db_index=True -> unique=True later in the same migration.
        migrations.AddField(
            model_name="order",
            name="tracking_code",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=32,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="item_tracking_code",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=32,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(fill_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="tracking_code",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=32,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="item_tracking_code",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=32,
                unique=True,
            ),
        ),
    ]
