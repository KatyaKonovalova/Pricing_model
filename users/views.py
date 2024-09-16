from django.shortcuts import render

def login(request):
    return render(
        request,
        "login_old.html",
    )
