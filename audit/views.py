import csv
import os
from django.shortcuts import render, redirect

from config import settings
from .forms import AuditForm
from .models import Data


def home(request):
    if request.method == "POST":
        form = AuditForm(request.POST, request.FILES)
        if form.is_valid():
            # uploaded_file = request.FILES['file']
            # file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)

            audit_instance = form.save(commit=False)  # Не сохраняем пока в базу
            audit_instance.user = request.user  # Присваиваем пользователя
            audit_instance.save()  # Теперь сохраняем
            uploaded_file = audit_instance.file.path  # Получаем путь к файлу


            # with open(file_path, 'wb+') as destination:
            #     for chunk in uploaded_file.chunks():
            #         destination.write(chunk)

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
                        print(f"Ошибка при обработке строки: {row} - {e}")
                    except Exception as e:
                        print(f"Ошибка при сохранении в БД: {e}")
                        continue

            # Удаляем файл после обработки
            os.remove(uploaded_file)

            return redirect("audit:home")
        else:
            print(form.errors)
    else:
        form = AuditForm()

    return render(request, "home.html", {"form": form})
