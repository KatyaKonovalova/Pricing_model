import psycopg2
import pandas as pd
import plotly.graph_objs as go
import plotly.graph_objects as go

from datetime import datetime

from audit.calculates import get_all_products, add_trend_and_forecast, calculate_median_price
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





def graph(request):
    # Проверяем, что запрос отправлен методом POST (для отправки данных через форму)
    if request.method == 'POST':
        # Получаем значения из POST-запроса: название продукта, тип линии тренда и период прогноза
        product_name = request.POST.get('product_input', '').strip()
        trend_type = request.POST.get('trend_type', 'linear')
        forecast_period = request.POST.get('forecast_period', 7)

        # Проверяем, является ли введенный период числом, если нет — устанавливаем 7 по умолчанию
        if not forecast_period.isdigit():
            messages.error(request, "Пожалуйста, введите корректное количество дней для прогноза.")
            forecast_period = 7  # По умолчанию 7 дней

        forecast_period = int(forecast_period)
        data_entries = Data.objects.filter(product=product_name)

        # Если данные для выбранного продукта отсутствуют, выводим ошибку и возвращаем пустой график
        if not data_entries.exists():
            messages.error(request, f"Продукт '{product_name}' не найден.")
            return render(request, 'audit/graph.html', {
                'graph': '',
                'products': get_all_products(),
                'product_input': product_name,
                'forecast_period': forecast_period
            })

        try:
            # Рассчитываем медианные цены на основе данных
            x_values, y_values = calculate_median_price(data_entries)

            # Если недостаточно данных для построения графика, выводим сообщение об ошибке
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

        # Обработка исключений при построении графика
        except Exception as e:
            messages.error(request, f"Ошибка при построении графика: {e}")
            return render(request, 'audit/graph.html', {
                'graph': '',
                'products': get_all_products(),
                'product_input': product_name,
                'forecast_period': forecast_period
            })

        # Построение столбчатой диаграммы с медианными ценами
        bar_trace = go.Bar(
            x=x_values,
            y=y_values,
            name='Медианная цена',
            marker=dict(color='rgba(34, 139, 34, 0.9)'),
            width=0.5
        )

        # Построение линии тренда на основе прогнозируемых данных
        trend_trace = go.Scatter(
            x=extended_x_values,
            y=extended_y_values,
            mode='lines',
            name=f'{trend_type.capitalize()} линия тренда',
            line=dict(color='red', width=2)
        )

        # Создаем объект графика с двумя слоями: столбцы и линия тренда
        fig = go.Figure(data=[bar_trace, trend_trace])

        # Настройки графика: заголовок, метки осей, размер графика
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

        # Преобразование графика в HTML-код для вставки на веб-страницу
        graph_div = fig.to_html(full_html=False)

        # Возвращаем страницу с построенным графиком
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

    # Если метод запроса не POST, просто возвращаем страницу с пустым графиком и дефолтными значениями
    return render(request, 'audit/graph.html', {
        'graph': '',
        'products': get_all_products(),
        'product_input': '',
        'forecast_period': 7
    })

