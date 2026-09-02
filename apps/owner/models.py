from django.db import models


class OwnerSettings(models.Model):
    store_name = models.CharField(max_length=80, default="AVAN")
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=30, blank=True)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    operations_note = models.CharField(max_length=240, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Owner settings"
        verbose_name_plural = "Owner settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.store_name} owner settings"
