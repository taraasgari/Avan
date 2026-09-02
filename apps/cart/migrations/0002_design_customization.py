from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("cart", "0001_initial"),
        ("designs", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="cartitem",
            name="uniq_cart_variant",
        ),
        migrations.AddField(
            model_name="cartitem",
            name="design",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cart_items",
                to="designs.design",
            ),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="design_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=("cart", "variant", "design"),
                name="uniq_cart_variant_design",
                nulls_distinct=False,
            ),
        ),
    ]
