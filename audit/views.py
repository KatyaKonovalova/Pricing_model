import psycopg2
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.graph_objects as go

from datetime import datetime
from audit.calculates import get_all_products, calculate_price, add_trend_and_forecast
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
                db_settings = settings.DATABASES["default"]

                conn_db = psycopg2.connect(
                    dbname=db_settings["NAME"],
                    user=db_settings["USER"],
                    password=db_settings["PASSWORD"],
                    host=db_settings["HOST"] if db_settings["HOST"] else "localhost",
                    port=db_settings["PORT"] if db_settings["PORT"] else "5432",
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
                    cur.copy_from(
                        f,
                        "audit_data",
                        sep=",",
                        columns=[
                            "price",
                            "count",
                            "add_cost",
                            "company",
                            "product",
                            "user_id",
                            "upload_date",
                        ],
                    )
                conn_db.commit()

                # Закрытие соединения с БД
                conn_db.close()

                # Сообщение об успешной загрузке файла
                messages.success(request, "Файл успешно загружен и обработан.")

            except Exception as e:
                messages.error(request, f"Ошибка при обработке файла: {e}")
                print(e)

        else:
            messages.error(
                request, "Форма содержит ошибки. Проверьте данные и попробуйте снова."
            )
    else:
        form = AuditForm()

    return render(request, "home.html", {"form": form})


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def graph(request):
    if request.method == "POST":
        product_name = request.POST.get("product_input", "").strip()
        trend_type = request.POST.get("trend_type", "linear")
        price_type = request.POST.get("price_type", "median")  # Получаем тип цены
        forecast_period = request.POST.get("forecast_period", 7)

        if not forecast_period.isdigit():
            messages.error(
                request, "Пожалуйста, введите корректное количество дней для прогноза."
            )
            forecast_period = 7

        forecast_period = int(forecast_period)
        data_entries = Data.objects.filter(product=product_name)

        if not data_entries.exists():
            messages.error(request, f"Продукт '{product_name}' не найден.")
            return render(
                request,
                "audit/graph.html",
                {
                    "graph": "",
                    "products": get_all_products(),
                    "product_input": product_name,
                    "forecast_period": forecast_period,
                },
            )

        try:
            # Рассчитываем выбранный тип цены (медианная, минимальная или максимальная)
            x_values, y_values = calculate_price(data_entries, price_type)

            if len(x_values) == 0 or len(y_values) == 0:
                messages.error(request, "Недостаточно данных для построения графика.")
                return render(
                    request,
                    "audit/graph.html",
                    {
                        "graph": "",
                        "products": get_all_products(),
                        "product_input": product_name,
                        "forecast_period": forecast_period,
                    },
                )

            # Добавляем линию тренда и прогноз на указанный период
            (
                extended_x_values,
                extended_y_values,
                y_trend,
                forecast_min,
                min_date,
                forecast_max,
                max_date,
            ) = add_trend_and_forecast(x_values, y_values, forecast_period, trend_type)

        except Exception as e:
            messages.error(request, f"Ошибка при построении графика: {e}")
            return render(
                request,
                "audit/graph.html",
                {
                    "graph": "",
                    "products": get_all_products(),
                    "product_input": product_name,
                    "forecast_period": forecast_period,
                },
            )

        bar_trace = go.Bar(
            x=x_values,
            y=y_values,
            name=f"{price_type.capitalize()} цена",
            marker=dict(color="rgba(34, 139, 34, 0.9)"),
            width=0.5,
        )

        trend_trace = go.Scatter(
            x=extended_x_values,
            y=extended_y_values,
            mode="lines",
            name=f"{trend_type.capitalize()} линия тренда",
            line=dict(color="red", width=2),
        )

        fig = go.Figure(data=[bar_trace, trend_trace])

        fig.update_layout(
            title=f'{price_type.capitalize()} цены по продукту "{product_name}" с прогнозом на {forecast_period} дней',
            xaxis_title="Дата загрузки",
            yaxis_title=f"{price_type.capitalize()} цена",
            xaxis=dict(type="category"),
            yaxis=dict(rangemode="tozero"),
            height=600,
            width=900,
            margin=dict(l=20, r=20, t=50, b=20),
        )

        graph_div = fig.to_html(full_html=False)

        # Подготовка данных для таблицы
        table_data = list(
            zip(
                extended_x_values[-forecast_period:],
                extended_y_values[-forecast_period:],
            )
        )

        return render(
            request,
            "audit/graph.html",
            {
                "graph": graph_div,
                "products": get_all_products(),
                "product_input": product_name,
                "forecast_period": forecast_period,
                "table_data": table_data,  # Передаем все данные в шаблон
                "trend_type": trend_type,
                "price_type": price_type,
            },
        )

    return render(
        request,
        "audit/graph.html",
        {
            "graph": "",
            "products": get_all_products(),
            "product_input": "",
            "forecast_period": 7,
        },
    )
