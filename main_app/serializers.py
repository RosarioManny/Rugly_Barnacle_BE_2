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

  class Meta:
    model = CartItem
    fields = ['id', 'product', 'dimensions', 'product_name', 'product_price', 'quantity', 'subtotal', 'added_at']

  def get_subtotal(self, obj):
    return obj.quantity * obj.product.price
  
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
class CustomOrderSerializer(serializers.ModelSerializer):
  
  class Meta: 
    model = CustomOrder
    fields = ['customer_name', 'description', 'email', 'owner_notes', 'status']
    read_only_fields = ['reference_id', 'created_at']