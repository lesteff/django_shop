
from django.urls import path



from django.urls import path

from api.views import (test_api, ProductDetailAPIView, ProductListAPIView, ProductCreateAPIView,
                       set_cookie_example, get_cookie_example, ProductDeleteAPIView, ProductUpdateAPIView,
                       RegisterAPIView,SetDiscountAPIView,
                       OrderDetailAPIView, OrderCheckoutAPIView,CartClearAPIView, CartRemoveAPIView,
                       CartAddAPIView, CartDetailAPIView, CartUpdateAPIView, OrderListAPIView)

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



urlpatterns = [
    path('test/', test_api),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('products/', ProductListAPIView.as_view(), name='product-list'),
    path('products/create/', ProductCreateAPIView.as_view(), name='product-create'),
    path('products/delete/<int:product_id>/', ProductDeleteAPIView.as_view(), name='product-delete'),
    path('products/update/<int:product_id>/', ProductUpdateAPIView.as_view(), name='product-update'),

    path('set-cookie/', set_cookie_example),
    path('get-cookie/', get_cookie_example),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('register/', RegisterAPIView.as_view(), name='api_register'),
#     path('logout/', LogoutAPIView.as_view(), name='api_logout'),
    path("products/<int:pk>/discount", SetDiscountAPIView.as_view(), name='product_detail'),

    # Корзина
    path('cart/', CartDetailAPIView.as_view(), name='cart-detail'),
    path('cart/add/', CartAddAPIView.as_view(), name='cart-add'),
    path('cart/remove/', CartRemoveAPIView.as_view(), name='cart-remove'),
    path('cart/clear/', CartClearAPIView.as_view(), name='cart-clear'),
    path('cart/update/<int:item_id>/', CartUpdateAPIView.as_view(), name='cart-update'),

    # Заказы
    path('orders/', OrderListAPIView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailAPIView.as_view(), name='order-detail'),
    path('orders/checkout/', OrderCheckoutAPIView.as_view(), name='order-checkout'),
]