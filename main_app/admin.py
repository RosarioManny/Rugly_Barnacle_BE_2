# admin.py
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import *

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_primary', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />')
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'quantity', 'created_at', 'get_primary_image', 'id'] # < - this Columns of the item details
    list_filter = ['category', 'created_at', 'properties'] # < - this creates a filter sidebar
    search_fields = ['name', 'description'] # < - this creates a search bar. These are the parameters that it uses to look through
    inlines = [ProductImageInline]
    filter_horizontal = ['properties']
    
    # Add a method to display primary image in list view
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />')
        return "N/A"

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return mark_safe(f'<img src="{primary_image.image.url}" style="max-height: 50px; max-width: 50px;" />')
        # Fallback to first image if no primary
        first_image = obj.images.first()
        if first_image:
            return mark_safe(f'<img src="{first_image.image.url}" style="max-height: 50px; max-width: 50px;" />')
        return "N/A"
    
    # Optional: Show properties in list view
    def get_properties_list(self, obj):
        return ", ".join([p.display_name for p in obj.properties.all()])
    get_properties_list.short_description = 'Properties'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name']
    search_fields = ['name', 'display_name']

# Register other models
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(CustomOrder)