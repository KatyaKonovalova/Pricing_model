from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from win32ui import CreateView

from .forms import AuditForm
from .models import Audit


def home(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    audit = Audit.objects.all()
    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    return render(
        request,
        "home.html",
    )

# ToDo: Настроить присвоение пользователя загруженному файлу. С этим кодом вылезает ошибка. Видео 22.2
# class AuditCreateView(CreateView):
#     model = Audit
#     form_class = AuditForm
#     success_url = reverse_lazy("audit:home")
#
#     def form_valid(self, form):
#         audit = form.save(commit=False)
#         audit.user = self.request.user
#         audit.save()
#         audit.user.save()
#         return redirect("audit:home", audit.pk)
