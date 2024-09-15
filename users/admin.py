from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'profile_value')
    fieldsets = (
        (None, {'fields': ('profile_value', 'email', 'password')}),
    )
    search_fields = ('email',)

