from django.shortcuts import render

from .models import Audit


def home(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    audit = Audit.objects.all()
    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    return render(request,"home.html",)
