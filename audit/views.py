import csv
import os
from django.contrib import messages

from django.shortcuts import render, redirect
from django.utils import timezone

from config import settings
from .forms import UploadFileForm
from .models import Audit


def handle_uploaded_file(file):
    """
    Обработчик файла: сохраняет данные из CSV в базу и удаляет файл после обработки.
    """
    file_path = os.path.join(settings.MEDIA_ROOT, file.name)

    # Сохраняем файл временно на сервере
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    # Открываем файл и читаем его содержимое
    with open(file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Создаем новые записи в базе данных
            Audit.objects.create(
                price=row['price'],
                count=row['count'],
                add_cost=row['add_cost'],
                company=row['company'],
                product=row['product'],
                upload_date=timezone.now(),
            )

    # Удаляем файл после успешного чтения
    if os.path.exists(file_path):
        os.remove(file_path)


def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'])
            return render(request, 'home.html', {'form': UploadFileForm(), 'success': 'Файл успешно загружен!'})
        else:
            return render(request, 'home.html', {'form': form, 'error': 'Ошибка при загрузке файла!'})

    else:
        form = UploadFileForm()

    return render(request, 'home.html', {'form': form})

# def home(request):
#     if request.method == 'POST':
#         form = AuditForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()  # Сохраняем файл в базу данных и на диск
#             return render(request, 'home.html', {'form': AuditForm(), 'success': 'Файл успешно загружен!'})
#         else:
#             return render(request, 'home.html', {'form': form, 'error': 'Ошибка при загрузке файла!'})
#
#     # Для GET-запроса отображаем пустую форму
#     form = AuditForm()
#     return render(request, 'home.html', {'form': form})
