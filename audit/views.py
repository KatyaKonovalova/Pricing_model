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

                # Проверяем, что столбцы содержат корректные типы данных
                df[0] = pd.to_numeric(df[0], errors='coerce')  # Преобразование столбца price в float
                df = df.dropna(subset=[0])  # Удаляем строки, где price не может быть приведен к числу

                # Добавление user_id и даты загрузки
                df[5] = [request.user.id] * df.shape[0]
                df[6] = [datetime.now()] * df.shape[0]

                # Перезаписываем файл без заголовков
                df.to_csv(uploaded_file, index=False, header=False)

                # Копирование данных в базу данных
                cur = conn_db.cursor()
                with open(uploaded_file) as f:
                    cur.copy_from(f, 'audit_data', sep=',',
                                  columns=['price', 'count', 'add_cost', 'company', 'product', 'user_id',
                                           'upload_date'])

                conn_db.commit()
                cur.close()  # Закрываем курсор
                conn_db.close()  # Закрываем соединение с БД

                # Сообщение об успешной загрузке файла
                messages.success(request, 'Файл успешно загружен и обработан.')

            except Exception as e:
                # Обработка ошибки и вывод сообщения пользователю
                messages.error(request, f"Ошибка при обработке файла: {e}")
                print(f"Ошибка при обработке файла: {e}")

            return redirect("audit:home")
        else:
            # Если форма содержит ошибки
            messages.error(request, "Форма содержит ошибки. Проверьте данные и попробуйте снова.")
    else:
        form = AuditForm()

    # Отображение страницы с формой
    return render(request, "home.html", {"form": form})


'''

Надо создать еще один столбец с вычислением среднего значения в день загрузки файла
Лучше в коде прописать, что в таблице нужно выводить среднее значение по товару в день загрузки файла
и на основании этих данных рассчитывать модель ценообразования
'''

from django.shortcuts import render


import pandas as pd
import numpy as np
import plotly.graph_objs as go
from django.contrib import messages

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from django.shortcuts import render
from django.contrib import messages
from .models import Data

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from django.shortcuts import render
from django.contrib import messages
from .models import Data


import pandas as pd
import numpy as np
import plotly.graph_objects as go
from django.shortcuts import render
from django.contrib import messages
from .models import Data  # ваша модель данных

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


def add_trend_and_forecast(x_values, y_values, forecast_days, trend_type):
    """
    Добавляет линию тренда и прогноз на указанное количество дней (forecast_days).
    Возвращает также минимальное и максимальное значение прогноза с датами.
    """
    x_numeric = np.arange(len(x_values))

    if trend_type == 'linear':
        slope, intercept = np.polyfit(x_numeric, y_values, 1)
        y_trend = slope * x_numeric + intercept
        future_x = np.arange(len(x_values), len(x_values) + forecast_days)
        future_y = slope * future_x + intercept
    elif trend_type == 'polynomial':
        coefficients = np.polyfit(x_numeric, y_values, 2)
        y_trend = np.polyval(coefficients, x_numeric)
        future_x = np.arange(len(x_values), len(x_values) + forecast_days)
        future_y = np.polyval(coefficients, future_x)
    elif trend_type == 'average':
        y_trend = np.full(len(x_numeric), np.mean(y_values))
        future_x = np.arange(len(x_values), len(x_values) + forecast_days)
        future_y = np.full(forecast_days, np.mean(y_values))
    else:
        raise ValueError(f"Некорректный тип линии тренда: {trend_type}")

    extended_x_values = np.concatenate([x_numeric, future_x])
    extended_y_values = np.concatenate([y_trend, future_y])
    extended_x_dates = pd.date_range(start=x_values.iloc[0], periods=len(extended_x_values)).strftime('%Y-%m-%d')

    forecast_min = np.min(future_y)
    forecast_max = np.max(future_y)
    min_date = extended_x_dates[len(x_values) + np.argmin(future_y)]
    max_date = extended_x_dates[len(x_values) + np.argmax(future_y)]

    return extended_x_dates, extended_y_values, y_trend, forecast_min, min_date, forecast_max, max_date


def graph(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_input', '').strip()
        trend_type = request.POST.get('trend_type', 'linear')
        forecast_period = request.POST.get('forecast_period', 7)

        if not forecast_period.isdigit():
            messages.error(request, "Пожалуйста, введите корректное количество дней для прогноза.")
            forecast_period = 7  # По умолчанию 7 дней

        forecast_period = int(forecast_period)

        data_entries = Data.objects.filter(user=request.user, product=product_name)

        if not data_entries.exists():
            messages.error(request, f"Продукт '{product_name}' не найден.")
            return render(request, 'graph.html', {
                'graph': '',
                'products': get_all_products(),
                'product_input': product_name,
                'forecast_period': forecast_period
            })

        try:
            x_values, y_values = calculate_median_price(data_entries)

            if len(x_values) == 0 or len(y_values) == 0:
                messages.error(request, "Недостаточно данных для построения графика.")
                return render(request, 'graph.html', {
                    'graph': '',
                    'products': get_all_products(),
                    'product_input': product_name,
                    'forecast_period': forecast_period
                })

            extended_x_values, extended_y_values, y_trend, forecast_min, min_date, forecast_max, max_date = add_trend_and_forecast(
                x_values, y_values, forecast_period, trend_type
            )

        except Exception as e:
            messages.error(request, f"Ошибка при построении графика: {e}")
            return render(request, 'graph.html', {
                'graph': '',
                'products': get_all_products(),
                'product_input': product_name,
                'forecast_period': forecast_period
            })

        bar_trace = go.Bar(
            x=x_values,
            y=y_values,
            name='Медианная цена',
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
            title=f'Медианные цены по продукту "{product_name}" с прогнозом на {forecast_period} дней',
            xaxis_title='Дата загрузки',
            yaxis_title='Медианная цена',
            xaxis=dict(type='category'),
            yaxis=dict(rangemode='tozero'),
            height=600,
            width=900,
            margin=dict(l=20, r=20, t=50, b=20)
        )

        graph_div = fig.to_html(full_html=False)

        return render(request, 'audit/graph.html', {
            'graph': graph_div,
            'products': get_all_products(),
            'product_input': product_name,
            'forecast_period': forecast_period,
            'forecast_min': forecast_min,
            'min_date': min_date,
            'forecast_max': forecast_max,
            'max_date': max_date,
            'trend_type': trend_type
        })

    return render(request, 'audit/graph.html', {
        'graph': '',
        'products': get_all_products(),
        'product_input': '',
        'forecast_period': 7
    })


def get_all_products():
    return Data.objects.values_list('product', flat=True).distinct()
