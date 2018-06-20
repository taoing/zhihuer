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

from zhihu.views import index, question_detail, answer_detail, explore
from user.views import register, user_login, user_logout

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
]

# 第三方验证码url配置
urlpatterns += [path('captcha/', include('captcha.urls'))]