import psycopg2
import pandas as pd
from datetime import datetime
from django.contrib import messages
from django.shortcuts import render, redirect
from audit.forms import AuditForm
from audit.models import Data
import plotly.graph_objs as go


def home(request):
    if request.method == "POST":
        form = AuditForm(request.POST, request.FILES)
        if form.is_valid():
            audit_instance = form.save(commit=False)  # Не сохраняем пока в базу
            audit_instance.user = request.user  # Присваиваем пользователя
            audit_instance.save()  # Теперь сохраняем
            uploaded_file = audit_instance.file.path  # Получаем путь к файлу

            try:
                # Подключение к базе данных
                conn_db = psycopg2.connect(
                    dbname="diploma", user="postgres", password="12345", host="localhost"
                )

                # Загрузка данных из CSV файла
                df = pd.read_csv(uploaded_file, header=None)

                # Добавление user_id и даты загрузки
                df[5] = [request.user.id] * df.shape[0]
                df[6] = [datetime.now()] * df.shape[0]

                df.to_csv(uploaded_file, index=False, header=False)

                # Копирование данных в базу данных
                cur = conn_db.cursor()
                with open(uploaded_file) as f:
                    cur.copy_from(f, 'audit_data', sep=',',
                                  columns=['price', 'count', 'add_cost', 'company', 'product', 'user_id',
                                           'upload_date'])
                conn_db.commit()

                # Закрытие соединения с БД
                conn_db.close()

                # Сообщение об успешной загрузке файла
                messages.success(request, 'Файл успешно загружен и обработан.')

            except Exception as e:
                messages.error(request, f"Ошибка при обработке файла: {e}")
                print(e)

            return redirect("audit:home")
        else:
            messages.error(request, "Форма содержит ошибки. Проверьте данные и попробуйте снова.")
    else:
        form = AuditForm()

    return render(request, "home.html", {"form": form})


'''

Надо создать еще один столбец с вычислением среднего значения в день загрузки файла
Лучше в коде прописать, что в таблице нужно выводить среднее значение по товару в день загрузки файла
и на основании этих данных рассчитывать модель ценообразования
'''


def calculate_median_price(data_entries):
    """
    Рассчитывает медианную цену продуктов по дням загрузки.
    """
    # Преобразуем queryset в DataFrame для работы с pandas
    data = pd.DataFrame(list(data_entries.values('upload_date', 'price', 'product')))

    # Преобразуем дату в формат pandas и отбросим время (оставим только дату)
    data['upload_date'] = pd.to_datetime(data['upload_date']).dt.date

    # Преобразуем столбец 'price' в числовой формат, игнорируя некорректные значения
    data['price'] = pd.to_numeric(data['price'], errors='coerce')

    # Удаляем строки с NaN значениями в цене
    data = data.dropna(subset=['price'])

    if data.empty:
        print("Отладка: данные пусты после очистки")
        return [], []

    # Группируем данные по дате (без учета времени) и считаем медианную цену
    grouped_data = data.groupby('upload_date')['price'].median().reset_index()

    # Извлекаем даты и медианные цены
    x_values = grouped_data['upload_date']
    y_values = grouped_data['price']

    print("Отладка: сгруппированные данные с медианной ценой по дням")
    print(grouped_data)

    return x_values, y_values


import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


def add_trend_and_forecast(x_values, y_values, days_to_forecast=7):
    """
    Добавляет линию тренда и прогноз на основе линейной регрессии.
    Возвращает расширенные x и y значения с прогнозом.
    """
    # Преобразуем даты в числа для регрессии
    x_numeric = np.arange(len(x_values)).reshape(-1, 1)  # Преобразуем индексы в числовой вид

    # Полиномиальная регрессия (2-й порядок)
    poly = PolynomialFeatures(degree=2)
    x_poly = poly.fit_transform(x_numeric)

    model = LinearRegression()
    model.fit(x_poly, y_values)

    # Предсказание трендовой линии на исторические данные
    y_trend = model.predict(x_poly)

    # Прогнозирование на будущие дни
    future_x_numeric = np.arange(len(x_values), len(x_values) + days_to_forecast).reshape(-1, 1)
    future_x_poly = poly.transform(future_x_numeric)
    future_y_forecast = model.predict(future_x_poly)

    # Добавляем прогнозированные даты и значения
    future_dates = pd.date_range(start=x_values.iloc[-1], periods=days_to_forecast + 1, freq='D')[1:]

    # Объединяем данные для возвращения
    extended_x_values = pd.concat([x_values, pd.Series(future_dates)])
    extended_y_values = np.concatenate([y_trend, future_y_forecast])

    return extended_x_values, extended_y_values, y_trend


def graph(request):
    if request.method == 'POST':
        # Получаем продукт, введённый пользователем
        product_name = request.POST.get('product_input', '').strip()

        if not product_name:
            messages.error(request, "Пожалуйста, введите название продукта.")
            return render(request, 'audit/graph.html', {
                'graph': '',
                'products': get_all_products(),
                'product_input': product_name
            })

        # Фильтруем данные по введенному продукту
        data_entries = Data.objects.filter(user=request.user, product=product_name)

        if not data_entries.exists():
            messages.error(request, f"Продукт '{product_name}' не найден.")
            return render(request, 'audit/graph.html', {
                'graph': '',
                'products': get_all_products(),
                'product_input': product_name
            })

        try:
            # Рассчитываем медианные значения
            x_values, y_values = calculate_median_price(data_entries)

            if len(x_values) == 0 or len(y_values) == 0:
                messages.error(request, "Недостаточно данных для построения графика.")
                return render(request, 'audit/graph.html', {
                    'graph': '',
                    'products': get_all_products(),
                    'product_input': product_name
                })

            # Добавляем линию тренда и прогноз
            extended_x_values, extended_y_values, y_trend = add_trend_and_forecast(x_values, y_values)

        except Exception as e:
            messages.error(request, f"Ошибка при построении графика: {e}")
            return render(request, 'audit/graph.html', {
                'graph': '',
                'products': get_all_products(),
                'product_input': product_name
            })

        # Построение графика
        bar_trace = go.Bar(
            x=x_values,
            y=y_values,
            name='Медианная цена',
            marker=dict(color='rgba(34, 139, 34, 0.9)'),
            width=0.5
        )

        # Линия тренда
        trend_trace = go.Scatter(
            x=extended_x_values,
            y=extended_y_values,
            mode='lines',
            name='Линия тренда',
            line=dict(color='red', width=2)
        )

        fig = go.Figure(data=[bar_trace, trend_trace])

        fig.update_layout(
            title=f'Медианные цены по продукту "{product_name}" с прогнозом',
            xaxis_title='Дата загрузки',
            yaxis_title='Медианная цена',
            xaxis=dict(type='category'),
            yaxis=dict(rangemode='tozero')
        )

        graph_div = fig.to_html(full_html=False)

        return render(request, 'audit/graph.html', {
            'graph': graph_div,
            'products': get_all_products(),
            'product_input': product_name
        })

    # Если GET-запрос, отображаем пустую форму
    return render(request, 'audit/graph.html', {
        'graph': '',
        'products': get_all_products(),
        'product_input': ''
    })

def get_all_products():
    """Функция для получения всех уникальных наименований продуктов из базы данных."""
    return Data.objects.values_list('product', flat=True).distinct()
