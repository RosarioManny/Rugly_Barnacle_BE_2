from django.db import models

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
  description = models.TextField(max_length=400, blank=True, null=True)
  email = models.EmailField(max_length=64, null=True)
  size_with_price = models.CharField(
    max_length=10, 
    choices=PRICES, 
    default=PRICES[0][0], 
    verbose_name="Rug Size & Price Range"
  )
  created_at = models.DateTimeField(auto_now_add=True)
  # TODO: Create an Accepted / Rejected / Pending

  def __str__(self):
    return f"Custom order {self.id}: {self.email} - ({self.created_at.date()})"
  
# ------------------------------------------------------ PRODUCT ------------------------------------------------------

# 6. TODO:: Create ProductImage Model
# class ProductImage(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
#     image = models.ImageField(upload_to='products/')
#     is_primary = models.BooleanField(default=False)  # Mark the main image

#     def __str__(self):
#         return f"Image for {self.product.name}"
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