"""zhihuer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from zhihu.views import index, question_detail, answer_detail, explore, topic_list, topic_detail, add_follow_answer, cancel_follow_answer, comment_answer, follow_question\
    , collect_answer
from user.views import register, user_login, user_logout, user_confirm, resend_confirm_email, user_home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    # path('zhihu/', include('zhihu.urls', namespace='zhihu')),
    path('question/detail/<int:question_id>/', question_detail, name='question_detail'),
    path('answer/detail/<int:answer_id>/', answer_detail, name='answer_detail'),
    path('explore/', explore, name='explore'),

    # 用户
    path('register/', register, name='register'),
    path('login/', user_login, name='user_login'),
    path('logout/', user_logout, name='user_logout'),
    path('confirm/<str:token>/', user_confirm, name='user_confirm'),
    path('resend_confirm_email/', resend_confirm_email, name='resend_confirm_email'),
    path('user/<int:user_id>/', user_home, name='user_home'),

    path('topic_list/', topic_list, name='topic_list'),
    path('topic_detail/<int:topic_id>/', topic_detail, name='topic_detail'),

    path('answer/detail/<int:answer_id>/add_follow_answer/', add_follow_answer, name='add_follow_answer'),
    path('answer/detail/<int:answer_id>/cancel_follow_answer/', cancel_follow_answer, name='cancel_follow_answer'),
    path('answer/detail/<int:answer_id>/comment_answer/', comment_answer, name='comment_answer'),
    path('question/detail/<int:question_id>/follow_question/', follow_question, name='follow_question'),
    path('answer/detail/<int:answer_id>/collect_answer/', collect_answer, name='collect_answer'),
]

# 第三方验证码url配置
urlpatterns += [path('captcha/', include('captcha.urls'))]