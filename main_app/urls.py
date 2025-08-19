from django.urls import path
from .views import *
from .views.cartviews import CartView, Add

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
  # TODO :: Create categories/ route
  path('category/', CategoryView.as_view(), name='category'),
  # TODO :: Create properties/ route
  path('properties/', PropertiesView.as_view(), name='properties')
]