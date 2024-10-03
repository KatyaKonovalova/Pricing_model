import unittest
import numpy as np
import pandas as pd
import datetime

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from users.models import User
from audit.models import Audit, Data
from django.urls import reverse
from audit.views import calculate_price, add_trend_and_forecast
from datetime import datetime, timedelta
from django.contrib.messages import get_messages
from unittest.mock import patch


class AuditModelTest(TestCase):
    def setUp(self):
        # Создание пользователя без поля username
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpassword"
        )
        self.audit = Audit.objects.create(file="testfile.csv", user=self.user)

    def test_audit_creation(self):
        self.assertEqual(self.audit.user.email, "testuser@example.com")


class DataModelTest(TestCase):
    def setUp(self):
        # Создание пользователя без поля username
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpassword"
        )
        self.data = Data.objects.create(
            price=100.0,
            count=10,
            add_cost=50.0,
            company="TestCo",
            product="TestProduct",
            user=self.user,
        )

    def test_data_creation(self):
        self.assertEqual(self.data.user.email, "testuser@example.com")


class UserModelTest(TestCase):
    def test_user_creation(self):
        # Создание пользователя с email, password и profile_value
        user = User.objects.create_user(
            email="user@example.com", password="password", profile_value="Analyst"
        )
        self.assertEqual(user.email, "user@example.com")
        self.assertTrue(user.check_password("password"))
        self.assertEqual(user.profile_value, "Analyst")


class HomeViewTest(TestCase):

    def setUp(self):
        # Создаем пользователя для тестов
        self.user = get_user_model().objects.create_user(
            email="testuser@example.com", password="testpassword"
        )

    def test_valid_file_upload(self):
        # Аутентифицируем пользователя
        self.client.force_login(self.user)

        # Создаем тестовый CSV файл
        csv_file = SimpleUploadedFile(
            "test.csv", b"100,5,20,Company,Product\n", content_type="text/csv"
        )
        response = self.client.post(reverse("audit:home"), {"file": csv_file})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Audit.objects.exists())  # Проверяем, что файл был загружен

    def test_invalid_file_upload(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("audit:home"), {})

        self.assertEqual(response.status_code, 200)


class CalculatePriceTest(TestCase):
    def setUp(self):
        Data.objects.create(
            price=100,
            count=5,
            add_cost=20,
            company="CompanyA",
            product="ProductA",
            upload_date=datetime.now(),
        )
        Data.objects.create(
            price=200,
            count=3,
            add_cost=10,
            company="CompanyB",
            product="ProductA",
            upload_date=datetime.now(),
        )

    def test_calculate_median_price(self):
        data_entries = Data.objects.all()
        x_values, y_values = calculate_price(data_entries, "median")
        self.assertEqual(len(x_values), 1)
        self.assertEqual(len(y_values), 1)
        self.assertEqual(y_values[0], 150)  # Медианная цена


class TestAddTrendAndForecast(unittest.TestCase):

    def setUp(self):
        # Подготовка начальных данных
        start_date = datetime(2023, 1, 1)
        self.x_values = pd.Series([start_date + timedelta(days=i) for i in range(10)])
        self.y_values = np.array([10, 12, 13, 15, 16, 17, 19, 18, 20, 21])
        self.forecast_days = 5

    def test_linear_trend(self):
        # Тест для линейной линии тренда
        trend_type = "linear"
        result = add_trend_and_forecast(
            self.x_values, self.y_values, self.forecast_days, trend_type
        )

        # Проверка, что функция вернула ожидаемое количество значений
        self.assertEqual(len(result), 7)

        (
            extended_x_dates,
            extended_y_values,
            y_trend,
            forecast_min,
            min_date,
            forecast_max,
            max_date,
        ) = result

        # Проверка, что даты увеличены на количество прогнозируемых дней
        self.assertEqual(len(extended_x_dates), len(self.x_values) + self.forecast_days)

        # Проверка, что прогноз содержит значения
        self.assertEqual(
            len(extended_y_values), len(self.x_values) + self.forecast_days
        )

    def test_polynomial_trend(self):
        # Тест для полиномиальной линии тренда
        trend_type = "polynomial"
        result = add_trend_and_forecast(
            self.x_values, self.y_values, self.forecast_days, trend_type
        )

        # Проверка, что функция вернула ожидаемое количество значений
        self.assertEqual(len(result), 7)

        (
            extended_x_dates,
            extended_y_values,
            y_trend,
            forecast_min,
            min_date,
            forecast_max,
            max_date,
        ) = result

        # Проверка, что даты увеличены на количество прогнозируемых дней
        self.assertEqual(len(extended_x_dates), len(self.x_values) + self.forecast_days)

        # Проверка, что прогноз содержит значения
        self.assertEqual(
            len(extended_y_values), len(self.x_values) + self.forecast_days
        )

    def test_average_trend(self):
        # Тест для средней линии тренда
        trend_type = "average"
        result = add_trend_and_forecast(
            self.x_values, self.y_values, self.forecast_days, trend_type
        )

        # Проверка, что функция вернула ожидаемое количество значений
        self.assertEqual(len(result), 7)

        (
            extended_x_dates,
            extended_y_values,
            y_trend,
            forecast_min,
            min_date,
            forecast_max,
            max_date,
        ) = result

        # Проверка, что прогноз содержит значения
        self.assertEqual(len(extended_x_dates), len(self.x_values) + self.forecast_days)
        self.assertEqual(
            len(extended_y_values), len(self.x_values) + self.forecast_days
        )

    def test_invalid_trend_type(self):
        # Тест для проверки некорректного типа линии тренда
        trend_type = "invalid_type"
        with self.assertRaises(ValueError):
            add_trend_and_forecast(
                self.x_values, self.y_values, self.forecast_days, trend_type
            )


class GraphViewTest(TestCase):
    def setUp(self):
        # Создаем тестового пользователя и данные для продуктов
        self.client = Client()
        self.url = reverse(
            "audit:graph"
        )  # Укажите правильное название URL для метода graph
        self.product_name = "TestProduct"

        # Создаем пример данных в базе для тестирования
        Data.objects.create(
            price=100,
            count=5,
            add_cost=20,
            company="CompanyA",
            product="ProductA",
            upload_date=datetime.now(),
        )
        Data.objects.create(
            price=200,
            count=3,
            add_cost=10,
            company="CompanyB",
            product="ProductA",
            upload_date=datetime.now(),
        )

    @patch("audit.views.calculate_price")
    @patch("audit.views.add_trend_and_forecast")
    def test_graph_post_valid_data(
        self, mock_add_trend_and_forecast, mock_calculate_price
    ):
        # Настраиваем mock для calculate_price
        mock_calculate_price.return_value = (["2024-01-01", "2024-01-02"], [10, 15])
        # Настраиваем mock для add_trend_and_forecast
        mock_add_trend_and_forecast.return_value = (
            ["2024-01-01", "2024-01-02", "2024-01-03"],
            [10, 15, 17],
            [10, 15],
            10,
            "2024-01-03",
            17,
            "2024-01-03",
        )

        # Отправляем корректный POST-запрос
        response = self.client.post(
            self.url,
            {
                "product_input": self.product_name,
                "trend_type": "linear",
                "price_type": "median",
                "forecast_period": "7",
            },
        )

        # Проверяем, что запрос прошел успешно
        self.assertEqual(response.status_code, 200)

        # Вывод контекста для дебага
        print(f"Response context: {response.context}")

    def test_graph_post_invalid_forecast_period(self):
        # Отправляем запрос с некорректным forecast_period
        response = self.client.post(
            self.url,
            {
                "product_input": self.product_name,
                "trend_type": "linear",
                "price_type": "median",
                "forecast_period": "abc",  # Некорректное значение
            },
        )

        # Проверка, что был вызван механизм сообщений об ошибке
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "Пожалуйста, введите корректное количество дней для прогноза."
                in str(msg)
                for msg in messages
            )
        )

        # Убедимся, что страница рендерится заново
        self.assertEqual(response.status_code, 200)
        self.assertIn("graph", response.context)

    def test_graph_post_product_not_found(self):
        # Отправляем запрос с несуществующим продуктом
        response = self.client.post(
            self.url,
            {
                "product_input": "NonExistentProduct",
                "trend_type": "linear",
                "price_type": "median",
                "forecast_period": "7",
            },
        )

        # Проверка, что был вызван механизм сообщений об ошибке
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "Продукт 'NonExistentProduct' не найден." in str(msg)
                for msg in messages
            )
        )

        # Убедимся, что страница рендерится заново
        self.assertEqual(response.status_code, 200)
        self.assertIn("graph", response.context)

    @patch("audit.views.calculate_price")
    def test_graph_post_no_data(self, mock_calculate_price):
        # Настраиваем mock для calculate_price, возвращающий пустые данные
        mock_calculate_price.return_value = ([], [])

        # Отправляем корректный POST-запрос
        response = self.client.post(
            self.url,
            {
                "product_input": self.product_name,
                "trend_type": "linear",
                "price_type": "median",
                "forecast_period": "7",
            },
        )

        # Проверка сообщений об ошибке
        messages = list(get_messages(response.wsgi_request))
        for msg in messages:
            print(f"Message: {msg}")
