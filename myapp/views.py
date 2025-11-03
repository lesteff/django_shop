from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
import requests
from django.conf import settings
from django.contrib import messages

from .forms import RegisterForm
from .models import Product, Category, OrderItem, Order


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # хэшируем пароль
            user.save()
            login(request, user)  # сразу авторизуем пользователя
            return redirect('products')  # редирект на список товаров
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def products_view(request):
    categories = Category.objects.all()
    category_id = request.GET.get('category')

    products = Product.objects.all()
    if category_id:
        products = products.filter(category_id=category_id)

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'products.html', {
        'products': page_obj.object_list,  # Берем продукты из page_obj
        'categories': categories,
        'selected_category': category_id,
        'page_obj': page_obj,
    })

@login_required(login_url='/login/')
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})


@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    cart = request.session.get('cart', [])

    # Добавляем товар в корзину (может быть несколько одинаковых)
    cart.append(product_id)
    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, 'Товар добавлен в корзину')
    return redirect('cart_view')


@login_required(login_url='/login/')
def remove_from_cart(request, product_id):
    """Удалить товар из корзины."""
    cart = request.session.get('cart', [])

    # Удаляем только одно вхождение товара
    if product_id in cart:
        cart.remove(product_id)
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Товар удален из корзины')

    return redirect('cart_view')

@login_required(login_url='/login/')
def cart_view(request):
    """Показать корзину."""
    cart = request.session.get('cart', [])

    if not cart:
        return render(request, 'cart.html', {'cart_items': [], 'total': 0})

    # Подсчитываем количество каждого товара
    from collections import Counter
    cart_counter = Counter(cart)

    # Получаем товары и формируем корзину
    products = Product.objects.filter(id__in=cart_counter.keys())

    cart_items = []
    total = 0

    for product in products:
        quantity = cart_counter[product.id]
        item_total = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total': item_total
        })
        total += item_total

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total
    })


@login_required(login_url='/login/')
def checkout_view(request):
    """Оформление заказа с отправкой в Telegram"""
    cart = request.session.get('cart', [])

    if not cart:
        messages.error(request, 'Корзина пуста')
        return redirect('cart_view')

    # Подсчитываем товары и общую сумму
    product_counts = {}
    for product_id in cart:
        product_counts[product_id] = product_counts.get(product_id, 0) + 1

    products = Product.objects.filter(id__in=cart)
    cart_items = []
    total = 0

    for product in products:
        quantity = product_counts[product.id]
        item_total = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total': item_total
        })
        total += item_total

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        customer_name = request.POST.get('customer_name', '')

        if not phone_number:
            messages.error(request, 'Пожалуйста, укажите номер телефона')
            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'total': total,
                'phone_number': phone_number,
                'customer_name': customer_name,
            })

        try:
            # Создаем заказ
            order = Order.objects.create(
                user=request.user,
                phone_number=phone_number,
                customer_name=customer_name,
                total_amount=total
            )

            # Создаем элементы заказа
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['product'].price
                )

            # Отправляем уведомление в Telegram
            order_items = OrderItem.objects.filter(order=order)
            telegram_message = create_order_message(order, order_items)
            telegram_sent = send_telegram_notification(telegram_message)

            # Очищаем корзину
            request.session['cart'] = []
            request.session.modified = True

            if telegram_sent:
                messages.success(request, f'Заказ #{order.id} успешно оформлен! Уведомление отправлено.')
            else:
                messages.success(request, f'Заказ #{order.id} успешно оформлен! (Уведомление не отправлено)')

            return redirect('order_success', order_id=order.id)

        except Exception as e:
            messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')
            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'total': total,
                'phone_number': phone_number,
                'customer_name': customer_name,
            })

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total': total,
    })


@login_required(login_url='/login/')
def order_success(request, order_id):
    """Страница успешного оформления заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    return render(request, 'order_success.html', {
        'order': order,
        'order_items': order_items,
    })


def send_telegram_notification(message):
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


def create_order_message(order, items):
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
