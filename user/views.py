from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .models import User
from .forms import RegisterForm, LoginForm

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
                pass

    context = {}
    context['login_form'] = login_form
    return render(request, 'user/login.html', context)

def user_logout(request):
    logout(request)
    return redirect(reverse('index'))