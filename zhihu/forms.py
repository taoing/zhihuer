# -*- coding: utf-8 -*-

from django import forms

class CommentForm(forms.Form):
    comment = forms.CharField(label='评论', widget=forms.Textarea(attrs={'class':'form-control', 'rows':'3'}), required=True)