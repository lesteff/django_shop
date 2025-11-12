from http import client

from django.test import TestCase
from decimal import Decimal
from myapp.models import Product
from rest_framework import status
from rest_framework.test import APITestCase
from .serializers import ProductSerializer


# Create your tests here.


#Проверяем правильно ли начисляется НДС
class ProductTest(TestCase):
    def test_price_with_vat(self):
        product = Product(name='Phone', price=Decimal('100.00'))
        self.assertEqual(product.price_with_vat, Decimal('120.00'))

#Проверяем создается ли в базе данных
class ProductIntegrationTest(APITestCase):
    def test_create_product(self):
        data = {'name': 'MacBook', 'price': '1000'}
        response = self.client.post('/api/products/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(name='MacBook').exists())

    #проверяем создание продукта с отрицательной ценой
    def test_create_product_price_incorrect(self):
        data = {'name': 'MacBook', 'price': '-1000'}
        response = self.client.post('/api/products/create/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductListTest(APITestCase):
    def test_get_products(self):
        Product.objects.create(name='Phone', price='500.00')
        response = self.client.get('/api/products/')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Phone', str(response.data))


#Тестирование черного ящика
class ProductBlackBoxTests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Phone', price='500.00')
    #создание продукта
    def test_create_product(self):
        data = {'name': 'MacBook', 'price': '1000'}
        response = self.client.post('/api/products/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # Удаление продукта
    def test_delete_product(self):
        delete_url = f'/api/products/delete/{self.product.id}/'
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    #полное обновления продукта (PUT)
    def test_update_product_put(self):
        update_data = {
            'name': 'New Name',
            'price': '200.00',
            'description': '',
            'in_stock': True,
            'category': None
        }
        update_url = f'/api/products/update/{self.product.id}/'
        response = self.client.put(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'New Name')
        self.assertEqual(str(self.product.price), '200.00')

    #частичное обновления продукта (PATCH)
    def test_update_product_patch(self):
        update_data = {'name': 'New Name'}  # Обновляем только имя

        update_url = f'/api/products/update/{self.product.id}/'
        response = self.client.patch(update_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что обновилось только имя
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'New Name')
        self.assertEqual(str(self.product.price), '500.00')

#Тестирование белого ящика
class ProductWhiteBoxTests(APITestCase):
    def test_create_product(self):
        product = Product(name='Phone', price=Decimal('100.00'))
        result = product.price_with_vat
        self.assertEqual(result, Decimal('120.00'))


class ProductDetailAPITest(APITestCase):
    def test_get_product_detail(self):
        product = Product.objects.create(name='Phone', price='500.00')
        response = self.client.get(f'/api/products/{product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Phone', response.json()['name'])


#тест на редирект
class ProductViewTests(TestCase):
    def test_redirect_after_register(self):
        response = self.client.post('/register/',{
            'username': 'test',
            'password': '123',
            'password2': '123',
            'email': 'test@test.com',
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('', response['Location'])



