import os
import csv
import time
from datetime import datetime

import plotly.graph_objs as go
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

from django.contrib import messages
from django.shortcuts import render, redirect

from audit.forms import AuditForm
from audit.models import Data

import psycopg2

path_to_media = 'C:/Users/konov/py_project/Diplom_2/media'


def home(request):
    if request.method == "POST":
        form = AuditForm(request.POST, request.FILES)
        if form.is_valid():
            audit_instance = form.save(commit=False)  # Не сохраняем пока в базу
            audit_instance.user = request.user  # Присваиваем пользователя
            audit_instance.save()  # Теперь сохраняем
            uploaded_file = audit_instance.file.path  # Получаем путь к файлу

            try:
                # ToDo: параметры брать settings!
                conn_db = psycopg2.connect(
                    dbname="diploma", user="postgres", password="12345", host="localhost"
                )
                df = pd.read_csv(uploaded_file, header=None)
                df[5] = [request.user.id] * df.shape[0]
                df[6] = [datetime.now()] * df.shape[0]
                df.to_csv(uploaded_file, index=False, header=False)
                cur = conn_db.cursor()
                f = open(uploaded_file)
                cur.copy_from(f, 'audit_data', sep=',', columns=['price', 'count', 'add_cost', 'company', 'product', 'user_id', 'upload_date'])
                conn_db.commit()
                conn_db.close()
                # # Обработка файла (например, если это CSV)
                # with open(uploaded_file, newline="", encoding="utf-8") as csvfile:
                #     reader = csv.reader(csvfile)
                #     # Пропускаем первую строку (если она заголовок)
                #     next(reader, None)
                #     for row in reader:
                #         try:
                #             # Извлечение данных согласно полям модели
                #             price = float(row[0])  # преобразование str в float
                #             count = int(row[1])
                #             add_cost = float(row[2])
                #             company = row[3]
                #             product = row[4]
                #
                #             # Создание экземпляра модели
                #             Data.objects.create(
                #                 price=price,
                #                 count=count,
                #                 add_cost=add_cost,
                #                 company=company,
                #                 product=product,
                #                 user=request.user,
                #             )
                #
                #         except (ValueError, IndexError) as e:
                #             messages.error(request, f"Ошибка при обработке строки: {row} - {e}")
                #         except Exception as e:
                #             messages.error(request, f"Ошибка при сохранении в БД: {e}")
                #             continue
                #
                # # Удаляем файл после обработки
                # os.remove(uploaded_file)

                # Сообщение об успешной загрузке файла
                messages.success(request, 'Файл успешно загружен и обработан.')
            except Exception as e:
                messages.error(request, f"Ошибка при обработке файла: {e}")
                print(e)

                # Сообщение об успешном удалении файла
                if os.path.exists(uploaded_file):
                    try:
                        time.sleep(1)  # Небольшая задержка перед удалением файла
                        os.remove(uploaded_file)
                        messages.success(request, 'Файл успешно удалён.')
                    except Exception as e:
                        messages.error(request, f"Ошибка при удалении файла: {e}")
                else:
                    messages.error(request, "Файл для удаления не найден.")

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

def forecast_price(data_entries, forecast_days=10):
    # ToDo: Сделать, чтобы пользователь сам мог выбирать на сколько дней прогноз
    # ToDo: Надо ли делать, чтобы была возможность посмотреть прогноз для конкретной компании
    # ToDo: Надо ли делать гистограмму или графики, которые просто буду показывать данные в бд
    # Добавить кнопку возвращения на главную страницу
    """
    Прогнозирование цены продукта на основе данных из модели.

    :param data_entries: queryset с данными модели Data.
    :param forecast_days: количество дней для прогноза.
    :return: x_values_extended, y_values_extended - массивы для построения графика.
    """
    # Извлекаем даты и цены из записей
    x_values = [entry.upload_date for entry in data_entries]
    y_values = [entry.price for entry in data_entries]

    # Преобразуем даты в числовой формат для модели
    x_values_numeric = pd.to_datetime(x_values).map(pd.Timestamp.timestamp).values.reshape(-1, 1)
    y_values_numeric = np.array(y_values)

    if len(x_values_numeric) > 1:
        # Строим модель линейной регрессии
        model = LinearRegression()
        model.fit(x_values_numeric, y_values_numeric)

        # Прогнозируем на несколько дней вперед
        last_date = pd.to_datetime(x_values[-1])  # Последняя дата
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, forecast_days + 1)]

        future_x_numeric = pd.to_datetime(future_dates).map(pd.Timestamp.timestamp).values.reshape(-1, 1)
        future_y = model.predict(future_x_numeric)

        # Объединяем исторические данные и прогноз
        x_values_extended = np.append(x_values_numeric, future_x_numeric).reshape(-1)
        y_values_extended = np.append(y_values_numeric, future_y)
    else:
        # Если данных недостаточно, используем только исторические данные
        x_values_extended = x_values_numeric.reshape(-1)
        y_values_extended = y_values_numeric

    # Преобразуем числовые даты обратно в нормальные для графика
    x_dates_extended = pd.to_datetime(x_values_extended, unit='s')

    return x_dates_extended, y_values_extended

def graph(request):
    if request.method == 'POST':
        product_name = request.POST.get('product')
        x_axis = request.POST.get('x_axis', 'upload_date')
        y_axis = request.POST.get('y_axis', 'price')
        chart_type = request.POST.get('chart_type', 'scatter')  # Значение по умолчанию

        # Получаем данные из базы данных
        data_entries = Data.objects.filter(user=request.user)

        if product_name:
            data_entries = data_entries.filter(product=product_name)

        # Прогнозируем цену
        x_values_extended, y_values_extended = forecast_price(data_entries)

        # Построение графика
        if chart_type == 'bar':
            fig = go.Figure(data=[go.Bar(x=x_values_extended, y=y_values_extended)])
        elif chart_type == 'scatter':
            fig = go.Figure(data=[go.Scatter(x=x_values_extended, y=y_values_extended, mode='lines+markers')])
        elif chart_type == 'line':
            fig = go.Figure(data=[go.Scatter(x=x_values_extended, y=y_values_extended, mode='lines')])
        else:
            fig = go.Figure(data=[go.Scatter(x=x_values_extended, y=y_values_extended, mode='lines+markers')])

        fig.update_layout(title=f'Прогноз {y_axis} по {x_axis}', xaxis_title=x_axis, yaxis_title=y_axis)
        graph_div = fig.to_html(full_html=False)

        return render(request, 'audit/graph.html', {
            'graph': graph_div,
            'product': product_name
        })

    return render(request, 'audit/graph.html', {})
