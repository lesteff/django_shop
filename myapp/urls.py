from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path


from .views import products_view, product_detail, register_view, add_to_cart, cart_view, remove_from_cart, \
    checkout_view, order_success

urlpatterns = [
    path('', products_view, name='products'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('register/', register_view, name='register'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('cart/', cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('checkout/', checkout_view, name='checkout'),
    path('order/success/<int:order_id>/', order_success, name='order_success'),
]
