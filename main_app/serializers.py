from rest_framework import serializers
from .models import Product, Property, CartItem, Cart, CustomOrder, Category

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
    
# PRODUCT
class ProductSerializer(serializers.ModelSerializer):
  
  category = CategorySerializer(read_only=True)

  class Meta:
    model = Product
    fields = '__all__'

    properties = serializers.PrimaryKeyRelatedField(
    many=True, 
    queryset=Property.objects.all()
  )
    
# CART

class CartSerializer(serializers.ModelSerializer):

  class Meta:
    model = Cart
    fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):

  class Meta:
    model = CartItem
    fields = ['id', 'product', 'quantity']

# CUSTOM 
class CustomOrderSerializer(serializers.ModelSerializer):
  
  class Meta: 
    model = CustomOrder
    fields = '__all__'