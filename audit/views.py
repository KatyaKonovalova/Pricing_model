import psycopg2
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.graph_objects as go

from datetime import datetime
from django.shortcuts import redirect
from audit.forms import AuditForm
from audit.models import Data
from django.shortcuts import render
from django.contrib import messages

from config import settings


def home(request):
    if request.method == "POST":
        form = AuditForm(request.POST, request.FILES)
        if form.is_valid():
            audit_instance = form.save(commit=False)  # Не сохраняем пока в базу
            audit_instance.user = request.user  # Присваиваем пользователя
            audit_instance.save()  # Теперь сохраняем
            uploaded_file = audit_instance.file.path  # Получаем путь к файлу

            try:
                # Подключение к базе данных на основе settings.py
                db_settings = settings.DATABASES['default']

                conn_db = psycopg2.connect(
                    dbname=db_settings['NAME'],
                    user=db_settings['USER'],
                    password=db_settings['PASSWORD'],
                    host=db_settings['HOST'] if db_settings['HOST'] else 'localhost',
                    port=db_settings['PORT'] if db_settings['PORT'] else '5432'
                    # Укажите 5432 по умолчанию, если порт не указан
                )

                # Чтение файла без заголовка для определения структуры
                df = pd.read_csv(uploaded_file, header=None)

                # Проверка первой строки: являются ли все ячейки строками (т.е. это может быть заголовок)
                contains_header = all(isinstance(cell, str) for cell in df.iloc[0])

                # Если это заголовок, удаляем первую строку
                if contains_header:
                    df = df[1:]

                # Добавление user_id и даты загрузки в файл
                df[5] = [request.user.id] * df.shape[0]
                df[6] = [datetime.now()] * df.shape[0]

                # Перезапись файла без заголовков (в случае их наличия)
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

        else:
            messages.error(request, "Форма содержит ошибки. Проверьте данные и попробуйте снова.")
    else:
        form = AuditForm()

    return render(request, "home.html", {"form": form})



def calculate_price(data_entries, price_type):
    """
    Рассчитывает медианную, минимальную или максимальную цену продуктов по дням загрузки в зависимости от выбранного типа цены.
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

    # Группируем данные по дате и рассчитываем нужный тип цены
    if price_type == 'median':
        grouped_data = data.groupby('upload_date')['price'].median().reset_index()
    elif price_type == 'min':
        grouped_data = data.groupby('upload_date')['price'].min().reset_index()
    elif price_type == 'max':
        grouped_data = data.groupby('upload_date')['price'].max().reset_index()
    else:
        raise ValueError(f"Некорректный тип цены: {price_type}")

    # Извлекаем даты и цены
    x_values = grouped_data['upload_date']
    y_values = grouped_data['price']

    print(f"Отладка: сгруппированные данные с {price_type} ценой по дням")
    print(grouped_data)

    return x_values, y_values



def add_trend_and_forecast(x_values, y_values, forecast_days, trend_type):
    """
    Добавляет линию тренда и прогноз на указанное количество дней (forecast_days).
    Возвращает также минимальное и максимальное значение прогноза с датами.
    """
    x_numeric = np.arange(len(x_values))

    # Выбор типа линии тренда
    if trend_type == 'linear':
        # Линейная регрессия
        slope, intercept = np.polyfit(x_numeric, y_values, 1)
        y_trend = slope * x_numeric + intercept

        # Прогноз на будущее
        future_x = np.arange(len(x_values), len(x_values) + forecast_days)
        future_y = slope * future_x + intercept

    elif trend_type == 'polynomial':
        # Полиномиальная регрессия
        coefficients = np.polyfit(x_numeric, y_values, 2)
        y_trend = np.polyval(coefficients, x_numeric)

        # Прогноз на будущее
        future_x = np.arange(len(x_values), len(x_values) + forecast_days)
        future_y = np.polyval(coefficients, future_x)

    elif trend_type == 'average':
        # Средняя линия тренда
        y_trend = np.full(len(x_numeric), np.mean(y_values))

        # Прогноз на будущее
        future_x = np.arange(len(x_values), len(x_values) + forecast_days)
        future_y = np.full(forecast_days, np.mean(y_values))

    else:
        raise ValueError(f"Некорректный тип линии тренда: {trend_type}")

    # Объединяем данные для отображения
    extended_x_values = np.concatenate([x_numeric, future_x])
    extended_y_values = np.concatenate([y_trend, future_y])

    # Преобразуем числовые значения обратно в даты для отображения
    extended_x_dates = pd.date_range(start=x_values.iloc[0], periods=len(extended_x_values)).strftime('%Y-%m-%d')

    # Минимальные и максимальные значения в прогнозе
    forecast_min = np.min(future_y)
    forecast_max = np.max(future_y)

    # Даты для минимальной и максимальной цены
    min_date = extended_x_dates[len(x_values) + np.argmin(future_y)]
    max_date = extended_x_dates[len(x_values) + np.argmax(future_y)]

    return extended_x_dates, extended_y_values, y_trend, forecast_min, min_date, forecast_max, max_date


def graph(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_input', '').strip()
        trend_type = request.POST.get('trend_type', 'linear')
        price_type = request.POST.get('price_type', 'median')  # Получаем тип цены
        forecast_period = request.POST.get('forecast_period', 7)

        if not forecast_period.isdigit():
            messages.error(request, "Пожалуйста, введите корректное количество дней для прогноза.")
            forecast_period = 7

        forecast_period = int(forecast_period)
        data_entries = Data.objects.filter(product=product_name)

        if not data_entries.exists():
            messages.error(request, f"Продукт '{product_name}' не найден.")
            return render(request, 'audit/graph.html', {
                'graph': '',
                'products': get_all_products(),
                'product_input': product_name,
                'forecast_period': forecast_period
            })

        try:
            # Рассчитываем выбранный тип цены (медианная, минимальная или максимальная)
            x_values, y_values = calculate_price(data_entries, price_type)

            if len(x_values) == 0 or len(y_values) == 0:
                messages.error(request, "Недостаточно данных для построения графика.")
                return render(request, 'audit/graph.html', {
                    'graph': '',
                    'products': get_all_products(),
                    'product_input': product_name,
                    'forecast_period': forecast_period
                })

            # Добавляем линию тренда и прогноз на указанный период
            extended_x_values, extended_y_values, y_trend, forecast_min, min_date, forecast_max, max_date = add_trend_and_forecast(
                x_values, y_values, forecast_period, trend_type
            )

        except Exception as e:
            messages.error(request, f"Ошибка при построении графика: {e}")
            return render(request, 'audit/graph.html', {
                'graph': '',
                'products': get_all_products(),
                'product_input': product_name,
                'forecast_period': forecast_period
            })

        bar_trace = go.Bar(
            x=x_values,
            y=y_values,
            name=f'{price_type.capitalize()} цена',
            marker=dict(color='rgba(34, 139, 34, 0.9)'),
            width=0.5
        )

        trend_trace = go.Scatter(
            x=extended_x_values,
            y=extended_y_values,
            mode='lines',
            name=f'{trend_type.capitalize()} линия тренда',
            line=dict(color='red', width=2)
        )

        fig = go.Figure(data=[bar_trace, trend_trace])

        fig.update_layout(
            title=f'{price_type.capitalize()} цены по продукту "{product_name}" с прогнозом на {forecast_period} дней',
            xaxis_title='Дата загрузки',
            yaxis_title=f'{price_type.capitalize()} цена',
            xaxis=dict(type='category'),
            yaxis=dict(rangemode='tozero'),
            height=600,
            width=900,
            margin=dict(l=20, r=20, t=50, b=20)
        )

        graph_div = fig.to_html(full_html=False)

        # Подготовка данных для таблицы
        table_data = list(zip(extended_x_values[-forecast_period:], extended_y_values[-forecast_period:]))

        return render(request, 'audit/graph.html', {
            'graph': graph_div,
            'products': get_all_products(),
            'product_input': product_name,
            'forecast_period': forecast_period,
            'table_data': table_data,
            'trend_type': trend_type,
            'price_type': price_type
        })

    return render(request, 'audit/graph.html', {
        'graph': '',
        'products': get_all_products(),
        'product_input': '',
        'forecast_period': 7
    })


# Функция для получения всех уникальных продуктов в базе данных
def get_all_products():
    return Data.objects.values_list('product', flat=True).distinct()