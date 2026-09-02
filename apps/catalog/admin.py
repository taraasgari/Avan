from django.contrib import admin
from .models import Category, Color, Product, ProductImage, ProductVariant, Size

admin.site.register([Category, Color, Size, Product, ProductImage, ProductVariant])
