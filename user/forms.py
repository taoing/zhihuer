# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from django import forms
from django.contrib.auth import authenticate
from captcha.fields import CaptchaField

from .models import User, CheckCode

class RegisterForm(forms.Form):
    username = forms.CharField(label="用户名", required=True, max_length=20)
    email = forms.EmailField(label="邮箱", max_length=40)
    password = forms.CharField(label="密码", widget=forms.PasswordInput)
    password2 = forms.CharField(label="重复密码", widget=forms.PasswordInput)
    captcha = CaptchaField(label='验证码')

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


class ForgetPwdForm(forms.Form):
    email = forms.EmailField(label='注册邮箱', widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder':'请输入你注册时的邮箱'}))
    password = forms.CharField(label='新密码', widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'新密码'}), min_length=6, max_length=36)
    password_2 = forms.CharField(label='重复新密码', widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'重复新密码'}), min_length=6, max_length=36)
    check_code = forms.CharField(label='验证码', widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'输入验证码'}))

    def clean_email(self):
        '''验证邮箱字段'''
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email):
            raise forms.ValidationError('该邮箱没有被注册, 请重新输入')
        return email

    def clean_password_2(self):
        '''验证码密码一致'''
        password = self.cleaned_data.get('password')
        password_2 = self.cleaned_data.get('password_2')
        if password != password_2:
            raise forms.ValidationError('两次密码输入不一致, 请重新输入')
        return password_2

    def clean_check_code(self):
        '''验证验证码是否正确'''
        email = self.cleaned_data.get('email')
        check_code = self.cleaned_data.get('check_code')
        user = User.objects.get(email=email)

        user_check_code = CheckCode.objects.filter(user=user)
        if user_check_code.count():
            user_check_code = user_check_code.first()
        else:
            raise forms.ValidationError('没有发送过验证码')
        # 验证码有效时间10分钟
        if datetime.now() > user_check_code.add_time + timedelta(seconds=10*60):
            raise forms.ValidationError('验证码失效')

        return check_code


class UserProfileForm(forms.ModelForm):
    '''用户资料修改表单'''
    class Meta:
        model = User
        fields = ['nickname', 'gender', 'description', 'address']
        '''
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class':'form-control'}),
            'nickname': forms.TextInput(attrs={'class':'form-control'}),
            'gender': forms.CheckboxInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'rows':3}),
            'address': forms.TextInput(attrs={'class':'form-control'}),
        }
        labels = {
            'image': '用户头像',
        }
        '''


class ChangePasswordForm(forms.Form):
    '''修改密码表单'''
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    old_password = forms.CharField(
        label='旧密码',
        min_length=6,
        max_length=36,
        widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'请输入你的旧密码'})
        )
    password = forms.CharField(
        label='新密码',
        min_length=6,
        max_length=36,
        widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'请输入你的新密码'})
        )
    password_2 = forms.CharField(
        label='新密码',
        min_length=6,
        max_length=36,
        widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'重复输入你的新密码'})
        )

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        user = authenticate(username = self.request.user.username, password=old_password)
        if not user:
            raise forms.ValidationError('密码错误')
        return old_password

    def clean_password_2(self):
        password = self.cleaned_data.get('password')
        password_2 = self.cleaned_data.get('password_2')
        if password != password_2:
            raise forms.ValidationError('两次密码输入不一致')
        return password_2


class ChangeEmailForm(forms.Form):
    '''修改邮箱表单'''
    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(ChangeEmailForm, self).__init__(*args, **kwargs)

    password = forms.CharField(
        label='输入密码',
        min_length=6,
        max_length=36,
        widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'请输入你的密码'})
        )
    new_email = forms.EmailField(
        label='新邮箱',
        widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder':'请输入你的新邮箱'})
        )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        user = authenticate(username=self.request.user.username, password=password)
        if not user:
            raise forms.ValidationError('密码错误')
        return password

    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email')
        if User.objects.filter(email=new_email):
            raise forms.ValidationError('该邮箱已被注册, 请重新输入')
        return new_email