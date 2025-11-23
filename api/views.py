import requests
from django.core.cache import cache
from django.db import transaction
from django.db.migrations import serializer
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, permissions, viewsets, generics
from rest_framework.authentication import TokenAuthentication

from rest_framework.decorators import api_view, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from myapp.models import Product, OrderItem, Category, Order
from rest_framework.views import APIView

from api.serializers import (ProductSerializer, RegisterSerializer, ProductDiscountSerializer,
                             CategorySerializer,CartItemSerializer,OrderSerializer, CheckoutSerializer)


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


    @method_decorator(cache_page(60*60))
    def get(self, request):
        print(">>>>>>>get")
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsManager]

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


# Корзина - переписываем на APIView
class CartDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить содержимое корзины"""
        cart = request.session.get('cart', {})

        if not cart:
            return Response({'cart_items': [], 'total': 0})

        cart_items = []
        total = 0

        product_ids = list(cart.keys())
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            quantity = cart[str(product.id)]
            item_total = product.price * quantity
            cart_items.append({
                'product': ProductSerializer(product).data,
                'quantity': quantity,
                'total': float(item_total)
            })
            total += item_total

        return Response({
            'cart_items': cart_items,
            'total': float(total)
        })


class CartAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Добавить товар в корзину"""
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            product_id = str(serializer.validated_data['product_id'])
            quantity = serializer.validated_data['quantity']

            cart = request.session.get('cart', {})

            if product_id in cart:
                cart[product_id] += quantity
            else:
                cart[product_id] = quantity

            request.session['cart'] = cart
            request.session.modified = True

            return Response({'message': 'Товар добавлен в корзину'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartRemoveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Удалить товар из корзины"""
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            product_id = str(serializer.validated_data['product_id'])
            quantity = serializer.validated_data.get('quantity', 1)

            cart = request.session.get('cart', {})

            if product_id in cart:
                if cart[product_id] <= quantity:
                    del cart[product_id]
                else:
                    cart[product_id] -= quantity

                request.session['cart'] = cart
                request.session.modified = True

                return Response({'message': 'Товар удален из корзины'})

            return Response({'error': 'Товар не найден в корзине'},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartClearAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """Очистить корзину"""
        request.session['cart'] = {}
        request.session.modified = True
        return Response({'message': 'Корзина очищена'})


# Заказы - переписываем на APIView
class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderCheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Оформление заказа"""
        cart = request.session.get('cart', {})

        if not cart:
            return Response(
                {'error': 'Корзина пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Подсчет общей суммы
                product_ids = list(cart.keys())
                products = Product.objects.filter(id__in=product_ids)

                total_amount = 0
                order_items_data = []

                for product in products:
                    quantity = cart[str(product.id)]
                    item_total = product.price * quantity
                    total_amount += item_total

                    order_items_data.append({
                        'product': product,
                        'quantity': quantity,
                        'price': product.price
                    })

                # Создание заказа
                order = Order.objects.create(
                    user=request.user,
                    phone_number=serializer.validated_data['phone_number'],
                    customer_name=serializer.validated_data.get('customer_name', ''),
                    total_amount=total_amount
                )

                # Создание элементов заказа
                for item_data in order_items_data:
                    OrderItem.objects.create(
                        order=order,
                        product=item_data['product'],
                        quantity=item_data['quantity'],
                        price=item_data['price']
                    )

                # Отправка в Telegram
                telegram_message = self.create_order_message(order, order.items.all())
                telegram_sent = self.send_telegram_notification(telegram_message)

                # Очистка корзины
                request.session['cart'] = {}
                request.session.modified = True

                response_data = {
                    'order_id': order.id,
                    'message': 'Заказ успешно оформлен',
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