# admin.py
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from .models import *

# ------------------------------------------------------ INLINE CLASSES ------------------------------------------------------
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

class CustomOrderImageInline(admin.TabularInline):
    model = CustomOrderImage
    extra = 1
    fields = ('image', 'image_preview', 'download_links')
    readonly_fields = ('image_preview', 'download_links')
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px; object-fit: contain;" />')
        return "No Image"
    image_preview.short_description = 'Preview'
    
    def download_links(self, obj):
        if obj.image:
            original_name = obj.image.name.split('/')[-1]  # Get filename
            links = []
            
            # Download original image
            if obj.image:
                links.append(
                    f'<a href="{obj.image.url}" download="{original_name}" style="display: block; width: fit-content; margin: 2px 0; padding: 4px 8px; background: #202254; color: white; text-decoration: none; border-radius: 3px; font-size: 12px;">'
                    f'Download Photo</a>'
                )
            
            return mark_safe(''.join(links))
        return "No file to download"
    download_links.short_description = 'Download'

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'added_at', 'subtotal']
    
    def subtotal(self, obj):
        return f"${obj.quantity * obj.product.price:.2f}"
    subtotal.short_description = 'Subtotal'

# ------------------------------------------------------ MODEL ADMIN CLASSES ------------------------------------------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'quantity', 'created_at', 'get_primary_image', 'id']
    list_filter = ['category', 'created_at', 'properties']
    search_fields = ['name', 'description']
    inlines = [ProductImageInline]
    filter_horizontal = ['properties']
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return mark_safe(f'<img src="{primary_image.image.url}" style="max-height: 50px; max-width: 50px;" />')
        first_image = obj.images.first()
        if first_image:
            return mark_safe(f'<img src="{first_image.image.url}" style="max-height: 50px; max-width: 50px;" />')
        return "N/A"
    get_primary_image.short_description = 'Image'

    def get_properties_list(self, obj):
        return ", ".join([p.display_name for p in obj.properties.all()])
    get_properties_list.short_description = 'Properties'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count']
    prepopulated_fields = {'slug': ['name',]}
    search_fields = ['name']
    
    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Products'

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'product_count']
    prepopulated_fields = {'name': ['display_name',]}
    search_fields = ['name', 'display_name']
    
    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Products'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_key', 'created_at', 'item_count', 'total_value']
    list_filter = ['created_at']
    search_fields = ['session_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'
    
    def total_value(self, obj):
        total = sum(item.quantity * item.product.price for item in obj.items.all())
        return f"${total:.2f}"
    total_value.short_description = 'Total Value'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity', 'subtotal', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__session_key', 'product__name']
    readonly_fields = ['added_at', 'subtotal_calc']
    
    def subtotal(self, obj):
        return f"${obj.quantity * obj.product.price:.2f}"
    subtotal.short_description = 'Subtotal'
    
    def subtotal_calc(self, obj):
        return f"${obj.quantity * obj.product.price:.2f}"
    subtotal_calc.short_description = 'Subtotal'

@admin.register(CustomOrder)
class CustomOrderAdmin(admin.ModelAdmin):
    list_display = ['reference_id', 'customer_name', 'email', 'contact_method', 'contact_info', 'status', 'created_at', 'image_count']
    list_filter = ['status', 'contact_method', 'created_at']
    search_fields = ['reference_id', 'customer_name', 'email', 'contact_info']
    readonly_fields = ['reference_id', 'created_at', 'images_preview']
    inlines = [CustomOrderImageInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('reference_id', 'created_at', 'status')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'email', 'contact_method', 'contact_info')
        }),
        ('Order Details', {
            'fields': ('description', 'admin_notes')
        }),
    )
    
    def image_count(self, obj):
        return obj.images.count()
    image_count.short_description = 'Images'
    
    def images_preview(self, obj):
        images = obj.images.all()[:5]
        if images:
            html = '<div style="display: flex; gap: 10px; flex-wrap: wrap;">'
            for image in images:
                if image.thumbnail:
                    html += f'<img src="{image.thumbnail.url}" width="100" height="100" style="object-fit: cover; border: 1px solid #ddd;" />'
                elif image.image:
                    html += f'<img src="{image.image.url}" width="100" height="100" style="object-fit: cover; border: 1px solid #ddd;" />'
            html += '</div>'
            return mark_safe(html)
        return "No images"
    images_preview.short_description = 'Reference Images Preview'

@admin.register(FaqModel)
class FaqAdmin(admin.ModelAdmin):
    list_display = ['question', 'answer', 'id']  
    search_fields = ['question', 'answer']
    list_display_links = ['question']  # <- Makes question clickable

@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_visible', 'created_at', 'id', 'image_preview']
    list_filter = ['created_at', 'is_visible']
    search_fields = ['title']
    list_editable = ['is_visible']  # <- Quick edit in list view

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 50px;" />')
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(BlogPost)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'tags', 'created_at']
    list_filter = ['tags', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']

@admin.register(Event)
class EventsAdmin(admin.ModelAdmin):
    list_display = ['status', 'title', 'location', 'status', 'event_type', 'price', 'start_time', 'end_time']
    search_fields = ['title', 'location', 'start_time', 'end_time', 'status', 'event_type']
    list_filter = ['title', 'location', 'start_time', 'end_time', 'status', 'event_type']
    ordering = ['-created_at', 'status', 'title', 'start_time']

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'subscribed_at', 'status']
    search_fields = ['email',]
    list_filter = ['subscribed_at', 'status']
    ordering = ['-subscribed_at']  
    list_per_page=60
    readonly_fields = ['subscribed_at']