from django.contrib.auth.forms import UserCreationForm
from django.forms import BooleanField

from audit.forms import StyleFormMixin
from users.models import User


class UserRegisterForm(UserCreationForm, StyleFormMixin):
    class Meta:
        model = User
        fields = ("email", "password1", "password2", "profile_value")
