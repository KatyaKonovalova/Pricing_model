import os
import csv
import time
import plotly.express as px
import plotly.graph_objs as go


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.shortcuts import render, redirect

from audit.forms import AuditForm
from audit.models import Data


def home(request):
    if request.method == "POST":
        form = AuditForm(request.POST, request.FILES)
        if form.is_valid():
            audit_instance = form.save(commit=False)  # Не сохраняем пока в базу
            audit_instance.user = request.user  # Присваиваем пользователя
            audit_instance.save()  # Теперь сохраняем
            uploaded_file = audit_instance.file.path  # Получаем путь к файлу

            try:
                # Обработка файла (например, если это CSV)
                with open(uploaded_file, newline="", encoding="utf-8") as csvfile:
                    reader = csv.reader(csvfile)
                    # Пропускаем первую строку (если она заголовок)
                    next(reader, None)
                    for row in reader:
                        try:
                            # Извлечение данных согласно полям модели
                            price = float(row[0])  # преобразование str в float
                            count = int(row[1])
                            add_cost = float(row[2])
                            company = row[3]
                            product = row[4]

                            # Создание экземпляра модели
                            Data.objects.create(
                                price=price,
                                count=count,
                                add_cost=add_cost,
                                company=company,
                                product=product,
                                user=request.user,
                            )

                        except (ValueError, IndexError) as e:
                            messages.error(request, f"Ошибка при обработке строки: {row} - {e}")
                        except Exception as e:
                            messages.error(request, f"Ошибка при сохранении в БД: {e}")
                            continue

                # Удаляем файл после обработки
                os.remove(uploaded_file)

                # Сообщение об успешной загрузке файла
                messages.success(request, 'Файл успешно загружен и обработан.')
            except Exception as e:
                messages.error(request, f"Ошибка при обработке файла: {e}")

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


def graph(request):
    if request.method == 'POST':
        product_name = request.POST.get('product')

        if product_name:
            data_entries = Data.objects.filter(product=product_name, user=request.user)

            # Пагинация
            paginator = Paginator(data_entries, 10)  # 10 записей на страницу

            page_number = request.GET.get('page')  # Получаем номер страницы из запроса
            try:
                page_obj = paginator.page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)  # Если номер страницы не целый, показываем первую страницу
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)  # Если номер страницы слишком большой, показываем последнюю

            # Извлечение данных для графика
            prices = [entry.price for entry in page_obj]
            companies = [entry.company for entry in page_obj]
            dates = [entry.upload_date for entry in page_obj]

            # Построение графиков
            # График столбиков относительно компаний
            bar_fig = go.Figure(data=[go.Bar(x=companies, y=prices)])
            bar_fig.update_layout(title=f'График цен на {product_name} по компаниям', xaxis_title='Компания',
                                  yaxis_title='Цена')
            bar_plot_div = bar_fig.to_html(full_html=False)

            # График Scatter относительно времени (дат)
            scatter_fig = go.Figure(data=[go.Scatter(x=dates, y=prices, mode='lines+markers')])
            scatter_fig.update_layout(title=f'График цен на {product_name} по времени', xaxis_title='Дата',
                                      yaxis_title='Цена')
            scatter_plot_div = scatter_fig.to_html(full_html=False)

            # Передача графиков в шаблон
            return render(request, 'audit/graph.html', {
                'bar_plot': bar_plot_div,
                'scatter_plot': scatter_plot_div,
                'product': product_name,
                'page_obj': page_obj
            })

        return render(request, 'audit/graph.html')