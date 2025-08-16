from django.contrib import admin 
from .models import Product, Property,Category, CartItem, Cart, CustomOrder

# Register your models here.
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(CustomOrder)
admin.site.register(Category)
admin.site.register(Property)