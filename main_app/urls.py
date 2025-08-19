from django.urls import path
from .views.homeview import Home
from .views.cartviews import CartView, AddtoCartView, CartItemDetailView
from .views.categoryviews import CategoryView
from .views.customOrdersviews import CustomOrderView
from .views.productviews import ProductList, ProductDetails
from .views.propertiesview import PropertiesView


urlpatterns = [
  path('', Home.as_view(), name='home'),
# PRODUCTS
  path('products/', ProductList.as_view(), name='product-list'),
  path('products/<int:id>', ProductDetails.as_view(), name='product-details'),

# CART
  path('cart/', CartView.as_view(), name='cart'),
  path('cart/items/', AddtoCartView.as_view(), name='add-to-cart'),
  path('cart/items/<int:id>', CartItemDetailView.as_view(), name='cart-item-detail'),

# CUSTOM ORDER
  path('custom/', CustomOrderView.as_view(), name='custom-order'),

# CATEGORY

  path('category/', CategoryView.as_view(), name='category'),
# PROPERTY
  path('properties/', PropertiesView.as_view(), name='properties')
]