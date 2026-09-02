from django.contrib import admin

from .models import AbandonedCartEvent, Campaign, CommerceSettings, FulfillmentEvent, Refund, ShippingRule

admin.site.register(CommerceSettings)
admin.site.register(ShippingRule)
admin.site.register(Campaign)
admin.site.register(AbandonedCartEvent)
admin.site.register(Refund)
admin.site.register(FulfillmentEvent)
