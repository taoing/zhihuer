from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.backends import ModelBackend #这是默认用户认证后端
from django.db.models import Q
from django.http import HttpResponse

from .models import User
from .forms import RegisterForm, LoginForm
from helper.send_email import send_email

class CustomModelBackend(ModelBackend):
    '''自定认证后端类, 重写ModelBackend的authenticate方法, 可以使用username和email同时登录'''
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 使用Q对象进行数据库or查询
        try:
            user = User.objects.get(Q(username=username)|Q(email=username))
            # 验证明文密码
            if user.check_password(password):
                return user
        except Exception as e:
            return None

def register(request):
    register_form = RegisterForm()
    if request.method == 'POST':
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user = User()
            user.username = register_form.cleaned_data.get('username')
            user.email = register_form.cleaned_data.get('email')
            user.set_password(register_form.cleaned_data.get('password'))
            user.save()

            # 生成账户确认签名
            token = user.generate_confirm_token()
            # 发送账户激活链接邮件
            send_email('知乎儿账户确认', 'user/email/user_confirm', user.email, user=user, token=token)
            # 网页显示账户注册成功消息
            messages.success(request, '账户已注册, 一封账户确认邮件已发往你的邮箱, 请查收')
            return redirect(reverse('user_login'))
        else:
            pass

    context = {}
    context['register_form'] = register_form
    return render(request, 'user/register.html', context)

def user_login(request):
    login_form = LoginForm()
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(reverse('index'))
            else:
                messages.warning(request, '用户名或密码错误')

    context = {}
    context['login_form'] = login_form
    return render(request, 'user/login.html', context)

def user_logout(request):
    '''退出登录'''
    logout(request)
    return redirect(reverse('index'))

def user_confirm(request, token):
    if request.user.confirmed:
        return redirect(reverse('index'))
    if request.user.confirm(token):
        messages.info(request, '你的账户已确认成功')
        return redirect(reverse('index'))
    else:
        messages.info(request, '确认链接无效或过期')
        return redirect(reverse('index'))

def resend_confirm_email(request):
    user = request.user
    token = user.generate_confirm_token()
    send_email('知乎儿账户确认', 'user/email/user_confirm', user.email, user=user, token=token)
    messages.info(request, '确认邮件已发送')
    return redirect(reverse('index'))