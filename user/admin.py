from django.contrib import admin

from .models import User, CheckCode

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'nickname', 'email')


class CheckCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'check_code', 'add_time')

admin.site.register(User, UserAdmin)
admin.site.register(CheckCode, CheckCodeAdmin)