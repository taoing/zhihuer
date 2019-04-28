from django.contrib import admin

from .models import User, CheckCode, UserRelationship


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'nickname', 'email')


class CheckCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'check_code', 'add_time')


class UserRelationshipAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'add_time')


admin.site.register(User, UserAdmin)
admin.site.register(CheckCode, CheckCodeAdmin)
admin.site.register(UserRelationship, UserRelationshipAdmin)
