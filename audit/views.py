from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from win32ui import CreateView

from .forms import AuditForm
from .models import Audit


# def home(request):
#     """
#     Функция отображения для домашней страницы сайта.
#     """
#     audit = Audit.objects.all()
#     # Отрисовка HTML-шаблона index.html с данными внутри
#     # переменной контекста context
#     return render(
#         request,
#         "home.html",
#     )

def home(request):
    if request.method == 'POST':
        form = AuditForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Сохраняем файл в базу данных и на диск
            return render(request, 'home.html', {'form': AuditForm(), 'success': 'Файл успешно загружен!'})
        else:
            return render(request, 'home.html', {'form': form, 'error': 'Ошибка при загрузке файла!'})

    # Для GET-запроса отображаем пустую форму
    form = AuditForm()
    return render(request, 'home.html', {'form': form})

