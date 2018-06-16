from django.contrib import admin

from .models import Topic, Question, Answer

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'pub_time')


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'author', 'get_answer', 'pub_time')

    def get_answer(self, obj):
        return obj.content[:50]
    get_answer.short_description = '回答内容' 


class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'add_time')


admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Topic, TopicAdmin)