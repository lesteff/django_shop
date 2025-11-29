import requests
from django.core.cache import cache
from django.db import transaction
from django.db.migrations import serializer
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, permissions, viewsets, generics
from rest_framework.authentication import TokenAuthentication

from rest_framework.decorators import api_view, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from myapp.models import Product, OrderItem, Category, Order, Cart, CartItem
from rest_framework.views import APIView

from api.serializers import (ProductSerializer, RegisterSerializer, ProductDiscountSerializer,
                             CategorySerializer,CartItemSerializer,OrderSerializer, CheckoutSerializer,
                             UpdateCartItemSerializer, CartSerializer, AddToCartSerializer)


from rest_framework_simplejwt.authentication import JWTAuthentication

from api.permissions import IsManager, IsClient

from django.conf import settings


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
    permission_classes = [IsAuthenticated, IsManager]

    @swagger_auto_schema(
        operation_summary="Список продуктов",
        operation_description="Получение списка продуктов с фильтрацией",
        responses={
            200: ProductSerializer(),

        }
    )


    @method_decorator(cache_page(60*60))
    def get(self, request):
        print(">>>>>>>get")
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsManager]
    @swagger_auto_schema(
        operation_summary="Создать продукт",
        operation_description="Создание нового товара. Требуются права менеджера",
        request_body=ProductSerializer,
        responses={
            201: """ Пример :
            
            {
                "id": 285,
                "name": "string",
                "description": "string",
                "price": "133.00",
                "in_stock": true,
                "category": 1,
                "image": null
            }""",

            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden'
        }
    )

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
    @swagger_auto_schema(
        operation_summary="Удалить продукт",
        operation_description="Удаление выбранного продукта",
        request_body=ProductSerializer,
        responses={
            204: """ Пример :
            
            {
                "product_id": 5,
                }""",

        }
    )
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsManager]
    def get_object(self, product_id):
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_summary="Обновить полностью",
        operation_description="Полное обновление товара",
        request_body=ProductSerializer,
        responses={
            200: """ Пример :
            
            {{
                "id": 285,
                "name": "string",
                "description": "string",
                "price": "133.00",
                "in_stock": true,
                "category": 1,
                "image": null
            }""",

        }
    )

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

    @swagger_auto_schema(
        operation_summary="Обновить частично",
        operation_description="Частичное обновление товара",
        request_body=ProductSerializer,
        responses={
            200: """ Пример :

                {{
                    "id": 285,
                    "name": "string",
                }""",

        }
    )


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

    @swagger_auto_schema(
        operation_summary="Регистрация",
        operation_description="Сваггер регистрации",
        request_body=RegisterSerializer,
        responses={
            201: RegisterSerializer(),
            400: 'Bad Request'
        }
    )

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


class SetDiscountAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def post(self, request, pk):
        product = Product.objects.get(pk=pk)

        serializer = ProductDiscountSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Discount updated",
                "product_id": product.id,
                "discount_percent": product.discount_percent
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Product.objects.all()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class CartDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить содержимое корзины"""
        cart, created = Cart.objects.get_or_create(user=request.user)

        if not cart.items.exists():
            return Response({'cart_items': [], 'total': 0, 'total_quantity': 0})

        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Добавить товар в корзину"""
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Товар не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )

            cart, created = Cart.objects.get_or_create(user=request.user)

            # Проверяем есть ли товар уже в корзине
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                # Если товар уже есть, увеличиваем количество
                cart_item.quantity += quantity
                cart_item.save()

            return Response({'message': 'Товар добавлен в корзину'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartRemoveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Удалить товар из корзины"""
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data.get('quantity', 1)

            cart = get_object_or_404(Cart, user=request.user)

            try:
                cart_item = CartItem.objects.get(cart=cart, product_id=product_id)

                if cart_item.quantity <= quantity:
                    # Удаляем полностью если количество меньше или равно
                    cart_item.delete()
                    message = 'Товар удален из корзины'
                else:
                    # Уменьшаем количество
                    cart_item.quantity -= quantity
                    cart_item.save()
                    message = f'Количество товара уменьшено на {quantity}'

                return Response({'message': message})

            except CartItem.DoesNotExist:
                return Response(
                    {'error': 'Товар не найден в корзине'},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartClearAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """Очистить корзину"""
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        return Response({'message': 'Корзина очищена'})


class CartUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        """Обновить количество товара в корзине"""
        serializer = UpdateCartItemSerializer(data=request.data)
        if serializer.is_valid():
            quantity = serializer.validated_data['quantity']

            cart = get_object_or_404(Cart, user=request.user)

            try:
                cart_item = CartItem.objects.get(id=item_id, cart=cart)
                cart_item.quantity = quantity
                cart_item.save()

                return Response({'message': 'Количество обновлено'})

            except CartItem.DoesNotExist:
                return Response(
                    {'error': 'Элемент корзины не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderListAPIView(generics.ListAPIView):
    """Список заказов пользователя"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items').order_by('-created_at')

class OrderDetailAPIView(generics.RetrieveAPIView):
    """Детали заказа"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderCheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Оформление заказа из корзины"""
        cart = get_object_or_404(Cart, user=request.user)

        if not cart.items.exists():
            return Response(
                {'error': 'Корзина пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Создание заказа
                order = Order.objects.create(
                    user=request.user,
                    phone_number=serializer.validated_data['phone_number'],
                    customer_name=serializer.validated_data.get('customer_name', ''),
                    total_amount=cart.total_price
                )

                # Создание элементов заказа из корзины
                for cart_item in cart.items.all():
                    # Используем цену с учетом скидки
                    item_price = cart_item.price_per_item

                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=item_price
                    )

                # Отправка в Telegram
                telegram_message = self.create_order_message(order, order.items.all())
                telegram_sent = self.send_telegram_notification(telegram_message)

                # Очистка корзины после оформления заказа
                cart.items.all().delete()

                response_data = {
                    'order_id': order.id,
                    'message': 'Заказ успешно оформлен',
                    'total_amount': float(order.total_amount),
                    'telegram_notification_sent': telegram_sent
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Ошибка при оформлении заказа: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create_order_message(self, order, items):
        """Формирует сообщение о заказе для Telegram"""
        items_text = "\n".join([
            f"• {item.product.name} - {item.quantity} шт. × {item.price} руб. = {item.get_total()} руб."
            for item in items
        ])

        message = f"""
🛒 <b>НОВЫЙ ЗАКАЗ #{order.id}</b>

👤 <b>Клиент:</b> {order.customer_name or 'Не указано'}
📞 <b>Телефон:</b> {order.phone_number}
💰 <b>Общая сумма:</b> {order.total_amount} руб.

<b>Состав заказа:</b>
{items_text}

⏰ <b>Время заказа:</b> {order.created_at.strftime('%d.%m.%Y в %H:%M')}
        """
        return message

    def send_telegram_notification(self, message):
        """Отправка сообщения в Telegram"""
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID

        if not bot_token or not chat_id:
            print("Telegram bot token or chat ID not configured")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, data=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")
            return False