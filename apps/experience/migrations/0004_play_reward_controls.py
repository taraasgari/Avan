from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('experience', '0003_rename_experience_game_score_idx_experience__game_id_5fd26f_idx_and_more'),
    ]

    operations = [
        migrations.AddField(model_name='sologame', name='bronze_discount_percent', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='sologame', name='silver_discount_percent', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='sologame', name='gold_discount_percent', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='sologame', name='bronze_subsidy_amount', field=models.DecimalField(decimal_places=0, default=0, max_digits=12)),
        migrations.AddField(model_name='sologame', name='silver_subsidy_amount', field=models.DecimalField(decimal_places=0, default=0, max_digits=12)),
        migrations.AddField(model_name='sologame', name='gold_subsidy_amount', field=models.DecimalField(decimal_places=0, default=0, max_digits=12)),
        migrations.AddField(model_name='sologame', name='reward_expiry_days', field=models.PositiveIntegerField(default=30)),
        migrations.AddField(model_name='challenge', name='reward_discount_percent', field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='challenge', name='reward_subsidy_amount', field=models.DecimalField(decimal_places=0, default=0, max_digits=12)),
        migrations.AddField(model_name='challenge', name='reward_expiry_days', field=models.PositiveIntegerField(default=30)),
    ]
