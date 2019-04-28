# -*- coding: utf-8 -*-

from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from .models import Topic


class CommentForm(forms.Form):
    '''回答评论表单'''
    comment = forms.CharField(label='评论', widget=forms.Textarea(
        attrs={'class': 'form-control', 'rows': '3'}), required=True)


class AskQuestionForm(forms.Form):
    '''提问表单'''
    title = forms.CharField(label='问题标题', widget=forms.TextInput(
        attrs={'class': 'form-control'}), max_length=200, required=True)
    topics = forms.ModelMultipleChoiceField(queryset=Topic.objects.all(),
                                            to_field_name='name', label='添加话题',
                                            required=True, \
                                            widget=forms.SelectMultiple(attrs={
                                                'class': 'selectpicker form-control',
                                                'data-live-search': 'true',
                                                'title': '请选择话题'}))
    content = forms.CharField(label='问题描述(可选)', widget=forms.Textarea(
        attrs={'class': 'form-control', 'rows': '3'}), required=False)
    anonymous = forms.BooleanField(label='匿名提问', required=False)


class AnswerForm(forms.Form):
    '''回答表单'''
    content = forms.CharField(label='回答', widget=CKEditorUploadingWidget(),
                              required=True)
    anonymous = forms.BooleanField(label='匿名回答', required=False)
