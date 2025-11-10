from rest_framework import serializers
from .models import *

# CATEGORY
class CategorySerializer(serializers.ModelSerializer):

  class Meta:
    model = Category
    fields = '__all__'

# PROPERTY
class PropertySerializer(serializers.ModelSerializer):
  class Meta:
    model = Property
    fields = '__all__'
    
# PRODUCT IMAGE 
class ProductImageSerializer(serializers.ModelSerializer):
  class Meta:
      model = ProductImage
      fields = ['id', 'image', 'thumbnail', 'is_primary']
      read_only_fields = ['id', 'thumbnail']

# PRODUCT
class ProductSerializer(serializers.ModelSerializer):
  category = CategorySerializer(read_only=True)
  images = ProductImageSerializer(
    many=True, 
    read_only=True
    )
  properties = serializers.PrimaryKeyRelatedField(
    many=True, 
    queryset=Property.objects.all()
    )


  class Meta:
    model = Product
    fields = '__all__'


# CART
class ItemSerializer(serializers.ModelSerializer):
  product_name  = serializers.CharField(source='product.name', read_only=True)
  product_price = serializers.DecimalField(
      source='product.price',
      max_digits=10,
      decimal_places=2, 
      read_only=True
    )
  dimensions = serializers.CharField(source='product.dimensions', read_only=True)
  subtotal = serializers.SerializerMethodField()
  product_images = serializers.SerializerMethodField()

  class Meta:
    model = CartItem
    fields = ['id', 'product', 'dimensions', 'product_images', 'product_name', 'product_price', 'quantity', 'subtotal', 'added_at']

  def get_subtotal(self, obj):
    return obj.quantity * obj.product.price
  
  def get_product_images(self, obj):
    images = obj.product.images.all()

    if images.exists():
      primary_image = images.filter(is_primary=True).first()
      if primary_image:
        return {
          'primary': primary_image.image.url,
          'thumbnail': primary_image.thumbnail.url if primary_image.thumbnail else None 
        }
      first_image = images.first()
      return {
              'primary': first_image.image.url,
              'thumbnail': first_image.thumbnail.url if first_image.thumbnail else None
          }
    return None
  

class CartSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'session_key', 'created_at', 'updated_at', 'items', 'total', 'item_count']
    
    def get_total(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())
    
    def get_item_count(self, obj):
        return obj.items.count()
    
# CUSTOM 
class CustomOrderImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomOrderImage
        fields = ['id', 'image', 'thumbnail', 'uploaded_at']
        read_only_fields = ['id', 'thumbnail', 'uploaded_at']

class CustomOrderSerializer(serializers.ModelSerializer):
    images = CustomOrderImageSerializer(many=True, read_only=True)
    image_count = serializers.SerializerMethodField()
    
    class Meta: 
        model = CustomOrder
        fields = [
            'reference_id', 'customer_name', 'description', 'email', 
            'contact_method', 'contact_info', 'admin_notes', 'status', 
            'created_at', 'images', 'image_count'
        ]
        read_only_fields = ['reference_id', 'created_at']
    
    def get_image_count(self, obj):
        return obj.images.count()
    
# FAQ
class FaqSerializer(serializers.ModelSerializer):
  class Meta:
    model = FaqModel
    fields = '__all__'

#PORTFOLIO
class PortfolioSerializer(serializers.ModelSerializer):
  class Meta:
    model = PortfolioImage
    fields = ['title', 'image', 'is_visible', 'created_at', 'id', 'thumbnail']
    read_only_fields = ['id', 'created_at']

# BLOGS
class BlogSerializer(serializers.ModelSerializer):
  class Meta: 
    model = BlogPost
    fields = ['title', 'tags', 'content', 'created_at', 'links', 'id']
    read_only_fields = ['created_at']
