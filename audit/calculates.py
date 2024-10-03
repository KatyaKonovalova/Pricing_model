import pandas as pd
import numpy as np
from audit.models import Data


def calculate_price(data_entries, price_type):
    """
    Рассчитывает медианную, минимальную или максимальную цену продуктов по дням загрузки в зависимости от выбранного типа цены.
    """
    # Преобразуем queryset в DataFrame для работы с pandas
    data = pd.DataFrame(list(data_entries.values("upload_date", "price", "product")))

    # Преобразуем дату в формат pandas и отбросим время (оставим только дату)
    data["upload_date"] = pd.to_datetime(data["upload_date"]).dt.date

    # Преобразуем столбец 'price' в числовой формат, игнорируя некорректные значения
    data["price"] = pd.to_numeric(data["price"], errors="coerce")

    # Удаляем строки с NaN значениями в цене
    data = data.dropna(subset=["price"])

    # Группируем данные по дате и рассчитываем нужный тип цены
    if price_type == "median":
        grouped_data = data.groupby("upload_date")["price"].median().reset_index()
    elif price_type == "min":
        grouped_data = data.groupby("upload_date")["price"].min().reset_index()
    elif price_type == "max":
        grouped_data = data.groupby("upload_date")["price"].max().reset_index()
    else:
        raise ValueError(f"Некорректный тип цены: {price_type}")

    # Извлекаем даты и цены
    x_values = grouped_data["upload_date"]
    y_values = grouped_data["price"]

    return x_values, y_values


def add_trend_and_forecast(x_values, y_values, forecast_days, trend_type):
    """
    Добавляет линию тренда и прогноз на указанное количество дней (forecast_days).
    Возвращает также минимальное и максимальное значение прогноза с датами.
    """
    x_numeric = np.arange(len(x_values))

    # Выбор типа линии тренда
    if trend_type == "linear":
        # Линейная регрессия
        slope, intercept = np.polyfit(x_numeric, y_values, 1)
        y_trend = slope * x_numeric + intercept

        # Прогноз на будущее
        future_x = np.arange(len(x_values), len(x_values) + forecast_days)
        future_y = slope * future_x + intercept

    elif trend_type == "polynomial":
        # Полиномиальная регрессия
        coefficients = np.polyfit(x_numeric, y_values, 2)
        y_trend = np.polyval(coefficients, x_numeric)

        # Прогноз на будущее
        future_x = np.arange(len(x_values), len(x_values) + forecast_days)
        future_y = np.polyval(coefficients, future_x)

    elif trend_type == "average":
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
    extended_x_dates = pd.date_range(
        start=x_values.iloc[0], periods=len(extended_x_values)
    ).strftime("%Y-%m-%d")

    # Минимальные и максимальные значения в прогнозе
    forecast_min = np.min(future_y)
    forecast_max = np.max(future_y)

    # Даты для минимальной и максимальной цены
    min_date = extended_x_dates[len(x_values) + np.argmin(future_y)]
    max_date = extended_x_dates[len(x_values) + np.argmax(future_y)]

    return (
        extended_x_dates,
        extended_y_values,
        y_trend,
        forecast_min,
        min_date,
        forecast_max,
        max_date,
    )


# Функция для получения всех уникальных продуктов в базе данных
def get_all_products():
    return Data.objects.values_list("product", flat=True).distinct()
