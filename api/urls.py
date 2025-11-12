from django.urls import path



from django.urls import path

from api.views import (test_api, ProductDetailAPIView, ProductListAPIView, ProductCreateAPIView,
                       set_cookie_example, get_cookie_example, ProductDeleteAPIView, ProductUpdateAPIView)




urlpatterns = [
    path('test/', test_api),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('products/', ProductListAPIView.as_view(), name='product-list'),
    path('products/create/', ProductCreateAPIView.as_view(), name='product-create'),
    path('products/delete/<int:product_id>/', ProductDeleteAPIView.as_view(), name='product-delete'),
    path('products/update/<int:product_id>/', ProductUpdateAPIView.as_view(), name='product-update'),

    path('set-cookie/', set_cookie_example),
    path('get-cookie/', get_cookie_example),
]