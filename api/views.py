from django.core.cache import cache
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication

from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from myapp.models import Product
from rest_framework.views import APIView

from api.serializers import ProductSerializer, RegisterSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication


# Create your views here.

@api_view(['GET'])
def test_api(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)
    return Response({
        'id': product.id,
        'name': product.name,
        'price': product.price,
    })

class ProductDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)
        return Response({
            'id': product.id,
            'name': product.name,
            'price': product.price,
        })



class ProductListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


    @method_decorator(cache_page(60*60))
    def get(self, request):
        print(">>>>>>>get")
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.clear_product_list_cache()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def clear_product_list_cache(self):
        cache_key = 'products_list_cache'
        cache.delete(cache_key)
        print(">>>>>>> Кэш очищен")


class ProductDeleteAPIView(APIView):
    def delete(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            product.delete()
            return Response(
                {"message": "Продукт успешно удален"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Product.DoesNotExist:
            return Response(
                {"error": "Продукт не найден"},
                status=status.HTTP_404_NOT_FOUND
            )


class ProductUpdateAPIView(APIView):
    def get_object(self, product_id):
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return None

    def put(self, request, product_id):
        product = self.get_object(product_id)
        if product is None:
            return Response(
                {"error": "Продукт не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, product_id):
        product = self.get_object(product_id)
        if product is None:
            return Response(
                {"error": "Продукт не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def set_cookie_example(request):
    response = Response({'message': 'Cookie установлено'})
    response.set_cookie(
        key='user_token',
        value='12345abcdef',
        max_age=15,  # 1 час
        httponly=True  # запрещает доступ к cookie из JS
    )
    return response


@api_view(['GET'])
def get_cookie_example(request):
    token = request.COOKIES.get('user_token')
    if token:
        return Response({'message': 'Cookie найден', 'token': token})
    return Response({'message': 'Cookie не найден'}, status=404)


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
