from django.urls import path
from .views.homeview import Home
from .views.cartviews import CartView, AddtoCartView, CartItemDetailView, RemoveFromCartView
from .views.categoryviews import CategoryView
from .views.customOrdersviews import CustomOrderView, CustomOrderDetailView
from .views.productviews import ProductList, ProductDetails
from .views.propertiesview import PropertiesView
from .views.faqview import FaqList


urlpatterns = [
  path('', Home.as_view(), name='home'),
# PRODUCTS
  path('products/', ProductList.as_view(), name='product-list'),
  path('products/<int:id>/', ProductDetails.as_view(), name='product-details'),

# CART
  path('cart/', CartView.as_view(), name='cart'),
  path('cart/add-to-cart/', AddtoCartView.as_view(), name='add-to-cart'),
  path('cart/items/<int:id>/', CartItemDetailView.as_view(), name='cart-item-detail'),
  path('cart/remove-from-cart/', RemoveFromCartView.as_view(), name="remove-from-cart"),

# CUSTOM ORDER
  path('custom/', CustomOrderView.as_view(), name='custom-order'),
  path('custom/<str:reference_id>/', CustomOrderDetailView.as_view(), name='custom-order-detail'),

# CATEGORY
  path('category/', CategoryView.as_view(), name='category'),

# PROPERTY
  path('properties/', PropertiesView.as_view(), name='properties'),

# FAQ
  path('faq/', FaqList.as_view(), name='faq'),
# PORTFOLIO
  path('portfolio/', PortfolioView.as_view(), name='portfolio')
]