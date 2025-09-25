from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from io import BytesIO
from PIL import Image
import os
import uuid

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
  description = models.TextField(max_length=400, blank=True, null=True)
  dimensions = models.CharField(max_length=40)
  quantity = models.PositiveIntegerField(default=1)
  properties = models.ManyToManyField(Property, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  # TODO: in_stock checker. 

  # Change the name of the display on admin panel
  def __str__(self):
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
  email = models.EmailField(max_length=250, blank=True, null=True)
  reference_id = models.CharField(max_length=20, unique=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  STATUS_CHOICE = [ 
    ('canceled', 'Canceled'),
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed')
  ]
  status = models.CharField(max_length=20, choices=STATUS_CHOICE, default='pending', blank=True, )
  owner_notes = models.TextField(blank=True, null=True)

  def save(self, *args, **kwargs):
    if not self.reference_id:
        self.reference_id = f"CUST-{uuid.uuid4().hex[:6].upper()}"
    super().save(*args, **kwargs)

  def __str__(self):
    return f"{self.reference_id}: {self.customer_name}"
  
# ------------------------------------------------------ PRODUCT ------------------------------------------------------

# 6. TODO:: Create ProductImage Model

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    thumbnail = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # First save to generate image path
        if not self.pk:
            super().save(*args, **kwargs)
        
        # Process image if it's new or changed
        if self.image:
            # Open the original image
            img = Image.open(self.image)
            
            # Resize main image if too large
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                
                # Save the resized image
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
            
            # Create thumbnail
            img.thumbnail((200, 200))
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
        
        # Ensure only one primary image per product
        if self.is_primary:
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