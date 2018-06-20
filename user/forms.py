# -*- coding: utf-8 -*-

from django import forms
from captcha.fields import CaptchaField

from .models import User

class RegisterForm(forms.Form):
    username = forms.CharField(label="用户名", required=True, max_length=20)
    email = forms.EmailField(label="邮箱", max_length=40)
    password = forms.CharField(label="密码", widget=forms.PasswordInput)
    password2 = forms.CharField(label="重复密码", widget=forms.PasswordInput)
    captcha = CaptchaField()

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password != password2:
            raise forms.ValidationError('密码不一致')
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).first():
            raise forms.ValidationError('用户已被使用, 请重新输入')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).first():
            raise forms.ValidationError('邮箱已被使用, 请重新输入')
        return email


class LoginForm(forms.Form):
    username = forms.CharField(label='用户名或邮箱', required=True, max_length=40)
    password = forms.CharField(label='密码', widget=forms.PasswordInput)