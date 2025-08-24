from django.contrib import admin 
from .models import Product, Property, Category, CartItem, Cart, CustomOrder

# Register your models here.
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(CustomOrder)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name']
    search_fields = ['name', 'display_name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'quantity', 'created_at']
    list_filter = ['category', 'created_at', 'properties']
    search_fields = ['name', 'description']
    filter_horizontal = ['properties']  # This adds the nice selector widget
    # OR use filter_vertical if you prefer vertical layout
    # filter_vertical = ['properties']
    
    # Optional: Show properties in list view
    def get_properties_list(self, obj):
        return ", ".join([p.display_name for p in obj.properties.all()])
    get_properties_list.short_description = 'Properties'