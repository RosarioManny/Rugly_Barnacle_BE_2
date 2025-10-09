from django.core.files.base import ContentFile
from django.db import models
# from django.utils import timezone
from io import BytesIO
from PIL import Image
import os
import uuid
from .services.email_service import OrderEmailService  

# To Create an enums or choice 
PRICES = (
    ('3ft', '$150-$249'),
    ('4ft', '$250-$349'),
    ('5ft', '$350-$449'),
    ('6ft +', '$450+'),
)

# ------------------------------------------------------ CATEGORY ------------------------------------------------------

class Category(models.Model):
    class Meta: 
        verbose_name_plural = "Categories"
        db_table = 'category'
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Property(models.Model):
    class Meta:
        db_table = 'properties'
    name = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=32)

    def __str__(self):
        return f"{self.id} - {self.display_name}"
# ------------------------------------------------------ PRODUCT ------------------------------------------------------

class Product(models.Model):
    class Meta:
        db_table = 'product'
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField(max_length=600, blank=True, null=True)
    dimensions = models.CharField(max_length=40)
    quantity = models.PositiveIntegerField(default=1)
    properties = models.ManyToManyField(Property, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # TODO: in_stock checker. 

    def __str__(self): # <- Change the name of the display on admin panel
        return f"Id: {self.id} - {self.name}"

# ------------------------------------------------------ CART ------------------------------------------------------

class Cart(models.Model):   
    session_key = models.CharField(max_length=48, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id} - ({self.created_at.date()})"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} - {self.added_at.month} / {self.added_at.day} / {self.added_at.year} - Cart: {self.cart.id} "
    
# ------------------------------------------------------ CUSTOM ------------------------------------------------------ 

class CustomOrder(models.Model):
    customer_name = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=400, blank=True, null=True)
    contact_method = models.CharField(
        max_length=20, 
        choices=[
            ('instagram', 'Instagram'),
            ('phone', 'Phone'),
            ('email', 'Email')
        ], 
        default='email'
    )
    contact_info = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=250, blank=True, null=True)
    reference_id = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICE = [ 
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('declined', 'Declined')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICE, default='pending', blank=True, )
    admin_notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        old_status = None
        
        if not is_new: # <- Get old status if update
            old_instance = CustomOrder.objects.get(pk=self.pk)
            old_status = old_instance.status

        if not self.reference_id: # <- Generate reference_id if it doesn't exist
            self.reference_id = f"CUST-{uuid.uuid4().hex[:6].upper()}"

        super().save(*args, **kwargs)  # <- Save the model first

        if not is_new and old_status != self.status:
            OrderEmailService.send_status_update(self, old_status) # <- Status changed - send update
            
    def __str__(self):
        return f"{self.reference_id}: {self.customer_name} - {self.email}"
    
class CustomOrderImage(models.Model):
    custom_order = models.ForeignKey(CustomOrder, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='custom_orders/')
    thumbnail = models.ImageField(upload_to='custom_orders/thumbnails/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        
        is_new = not self.pk # <- Check if this is a new image (no primary key yet)
        
        if is_new:
            super().save(*args, **kwargs) # <- For new images, save first to get an ID
        
        if self.image: # <- Process images if the main image exists
            try:
                img = Image.open(self.image)
                
                
                if img.height > 800 or img.width > 800: # <- Resize main image if too large
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    
                    buffer = BytesIO()
                    if img.format == 'PNG':
                        img.save(buffer, format='PNG')
                        self.image.save(
                            os.path.splitext(self.image.name)[0] + '.png',
                            ContentFile(buffer.getvalue()),
                            save=False
                        )
                    else:
                        img.save(buffer, format='JPEG', quality=85)
                        self.image.save(
                            os.path.splitext(self.image.name)[0] + '.jpg',
                            ContentFile(buffer.getvalue()),
                            save=False
                        )
                
                
                img.thumbnail((200, 200)) # <- Create thumbnail
                thumb_buffer = BytesIO()
                if img.format == 'PNG':
                    img.save(thumb_buffer, format='PNG')
                    thumb_name = os.path.splitext(self.image.name)[0] + '_thumb.png'
                else:
                    img.save(thumb_buffer, format='JPEG', quality=75)
                    thumb_name = os.path.splitext(self.image.name)[0] + '_thumb.jpg'
                
                self.thumbnail.save(
                    thumb_name,
                    ContentFile(thumb_buffer.getvalue()),
                    save=False
                )
                
            except Exception as e:
                print(f"Error processing image: {e}") # <- Don't break the save if image processing fails      
    
    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"Image for {self.custom_order.reference_id}"

# ------------------------------------------------------ PRODUCT ------------------------------------------------------
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    thumbnail = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        
        if not self.pk: # <- First save to generate image path
            super().save(*args, **kwargs)
        
        
        if self.image: # <- Process image if it's new or changed
            
            img = Image.open(self.image) # <- Open the original image
            
            
            if img.height > 800 or img.width > 800: # <- Resize main image if too large
                output_size = (800, 800)
                img.thumbnail(output_size)
                
                
                buffer = BytesIO() # <- Save the resized image
                if img.format == 'PNG':
                    img.save(buffer, format='PNG')
                    self.image.save(
                        os.path.splitext(self.image.name)[0] + '.png',
                        ContentFile(buffer.getvalue()),
                        save=False
                    )
                else:
                    img.save(buffer, format='JPEG', quality=85)
                    self.image.save(
                        os.path.splitext(self.image.name)[0] + '.jpg',
                        ContentFile(buffer.getvalue()),
                        save=False
                    )
            
            
            img.thumbnail((200, 200)) # <- Create thumbnail
            thumb_buffer = BytesIO()
            if img.format == 'PNG':
                img.save(thumb_buffer, format='PNG')
                thumb_name = os.path.splitext(self.image.name)[0] + '_thumb.png'
            else:
                img.save(thumb_buffer, format='JPEG', quality=75)
                thumb_name = os.path.splitext(self.image.name)[0] + '_thumb.jpg'
            
            self.thumbnail.save(
                thumb_name,
                ContentFile(thumb_buffer.getvalue()),
                save=False
            )
        
        
        if self.is_primary: # <- Ensure only one primary image per product
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
            
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete associated files
        if self.image:
            self.image.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
# ------------------------------------------------------ FAQ ------------------------------------------------------
class FaqModel(models.Model):
    question = models.CharField(max_length=500, blank=True)
    answer = models.CharField(max_length=500)
# ------------------------------------------------------ PORTFOLIO ------------------------------------------------------

class PortfolioImage(models.Model):
    class Meta:
        db_table = 'portfolio images'
        verbose_name_plural = "Portfolio Images"
        ordering = ['-created_at']
    title = models.CharField(max_length=200, blank=True, help_text="Short description of the rug (e.g., 'Blue Geometric Pattern Rug')")
    image = models.ImageField(upload_to='portfolio/')
    is_visible = models.BooleanField(default=True, help_text="Toggle to show this in the portfolio")
    created_at = models.DateField(auto_now_add=True)
    thumbnail = models.ImageField(upload_to='portfolio/thumbnails/', blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk

        if is_new:
            super().save(*args, **kwargs)
        
        if self.image:
            try:
                img = Image.open(self.image)

                if img.height > 1200 or img.width > 1200:
                    output_size = (1200, 1200)
                    img.thumbnail(output_size)

                    buffer = BytesIO()
                    if img.format == 'PNG':
                        img.save(buffer, format='PNG')
                        self.image.save(
                            os.path.splitext(self.image.name)[0] + 'png',
                            ContentFile(buffer.getvalue()),
                            save=False
                        )
                    else:
                        img.save(buffer, format == 'JPG', quality=85)
                        self.image.save(
                            os.path.splitext(self.image.name)[0] + 'jpg',
                            ContentFile(buffer.getvalue()),
                            save=False
                        )
                
                img.thumbnail((400, 400)) # <- Create thumbnail
                thumb_buffer = BytesIO()
                if img.format == 'PNG':
                    img.save(thumb_buffer, format='PNG')
                    thumb_name = os.path.splitext(self.image.name)[0] + '_thumb.png'
                else:
                    img.save(thumb_buffer, format='JPEG', quality=75)
                    thumb_name = os.path.splitext(self.image.name)[0] + '_thumb.jpg'
                
                self.thumbnail.save(
                    thumb_name,
                    ContentFile(thumb_buffer.getvalue()),
                    save=False
                )
                
            except Exception as e:
                print(f"Error processing portfolio image: {e}")
                
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete associated files
        if self.image:
            self.image.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return self.title
"""
Make migrations::
> python manage.py makemigrations

>> How does models.ForeignKey Work? << 
1. Creates a Many-to-One relation. Creates a column in the db with the specified relations (Id). This case, Cartitem -> Cart(specifically Cart's Id)
2. Arg1 specifies what the relation is too. Ex: CartItems.cart is related Cart; CartItems.product is related to Product.
3. related_name refers to the inverse from Cart -> CartItem. 
  3a. Without: You'd use cart.cartitem_set.all()
      With: You use cart.items.all() (clearer)
4. on_delete defines what happens on delete. CASCADE refers to how it deletes; Delete all CartItems if their Cart is deleted.
"""