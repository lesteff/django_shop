from faker import Faker
import random
from .models import Product, Category

fake = Faker('ru_RU')


def run():
    # Более тематические категории для магазина электроники
    category_data = {
        'Ноутбуки': {
            'brands': ['Asus', 'Lenovo', 'HP', 'Dell', 'Acer', 'Apple', 'MSI'],
            'models': ['Ultra', 'Pro', 'Gaming', 'Standard', 'Elite', 'ThinkPad', 'MacBook'],
            'suffixes': ['15"', '17"', 'Air', 'Pro', 'Gaming', 'Workstation']
        },
        'Смартфоны': {
            'brands': ['Samsung', 'Apple', 'Xiaomi', 'Huawei', 'Realme', 'OnePlus', 'Google'],
            'models': ['Galaxy', 'iPhone', 'Redmi', 'Poco', 'Mate', 'Pixel', 'Nord'],
            'suffixes': ['Pro', 'Max', 'Lite', 'Ultra', 'Plus', '5G']
        },
        'Планшеты': {
            'brands': ['Apple', 'Samsung', 'Lenovo', 'Huawei', 'Xiaomi'],
            'models': ['iPad', 'Galaxy Tab', 'Tab', 'MatePad', 'Mi Pad'],
            'suffixes': ['Mini', 'Air', 'Pro', 'Lite', '10"', '12"']
        },
        'Наушники': {
            'brands': ['Sony', 'Apple', 'Samsung', 'JBL', 'Beats', 'Xiaomi', 'Marshall'],
            'models': ['Wireless', 'AirPods', 'Buds', 'Studio', 'QuietComfort'],
            'suffixes': ['Pro', 'Max', '3', '4', 'Plus']
        },
        'Аксессуары': {
            'brands': ['Baseus', 'UGREEN', 'Anker', 'Samsung', 'Apple', 'Xiaomi'],
            'models': ['Кабель', 'Зарядное устройство', 'Чехол', 'Внешний аккумулятор', 'Док-станция'],
            'suffixes': ['Fast Charge', 'Pro', 'Magnetic', 'Wireless', 'Type-C']
        }
    }

    # Создаём категории
    categories = []
    for cat_name in category_data.keys():
        cat, created = Category.objects.get_or_create(name=cat_name)
        categories.append(cat)
        print(f"Категория '{cat_name}' создана")

    # Создаём тематические продукты
    for _ in range(100):  # Увеличим количество товаров
        cat = random.choice(categories)
        cat_info = category_data[cat.name]

        brand = random.choice(cat_info['brands'])
        model = random.choice(cat_info['models'])
        suffix = random.choice(cat_info['suffixes'])

        # Формируем реалистичное название
        product_name = f"{brand} {model} {suffix}"

        # Генерируем реалистичные цены в зависимости от категории
        if cat.name == 'Ноутбуки':
            price = round(random.uniform(1500, 4000), 2)
        elif cat.name == 'Смартфоны':
            price = round(random.uniform(800, 5000), 2)
        elif cat.name == 'Планшеты':
            price = round(random.uniform(800, 5000), 2)
        elif cat.name == 'Наушники':
            price = round(random.uniform(20, 250), 2)
        else:  # Аксессуары
            price = round(random.uniform(5, 60), 2)

        # Генерируем тематическое описание
        descriptions = {
            'Ноутбуки': [
                f"Мощный {brand} {model} для работы и игр",
                f"Производительный ноутбук с отличной автономностью",
                f"Игровой ноутбук с современной видеокартой",
                f"Ультрабук для мобильных профессионалов"
            ],
            'Смартфоны': [
                f"Смартфон {brand} {model} с продвинутой камерой",
                f"Мощный флагман с большим временем работы",
                f"Стильный дизайн и высокая производительность",
                f"Инновационные функции и премиальная сборка"
            ],
            'Планшеты': [
                f"Универсальный планшет для работы и развлечений",
                f"Идеален для просмотра контента и творчества",
                f"Мощный процессор и яркий дисплей",
                f"Компактный и производительный"
            ],
            'Наушники': [
                f"Качественный звук и комфортная посадка",
                f"Продолжительное время работы от аккумулятора",
                f"Превосходное шумоподавление и чистота звука",
                f"Стильный дизайн и премиальные материалы"
            ],
            'Аксессуары': [
                f"Высокое качество и надежность",
                f"Совместимость с большинством устройств",
                f"Быстрая зарядка и безопасность",
                f"Стильный дизайн и практичность"
            ]
        }

        description = random.choice(descriptions[cat.name])

        # Добавляем детали к описанию
        features = [
            "Высокое качество сборки.",
            "Современный дизайн.",
            "Энергоэффективность.",
            "Простота в использовании.",
            "Гарантия производителя.",
            "Экологичные материалы."
        ]

        full_description = f"{description} {random.choice(features)}"

        # Создаем продукт
        Product.objects.create(
            name=product_name,
            description=full_description,
            price=price,
            in_stock=random.choice([True, True, True, False]),  # 75% chance in stock
            category=cat
        )

