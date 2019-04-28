# -*- coding: utf-8 -*-

from django.template import Library

register = Library()


# 表单widget使用as_widget()方法渲染
@register.filter(name='widget_add_class')
def widget_add_class(value, arg):
    return value.as_widget(attrs={'class': arg})


# 获取对象的类名
# 在模板中不能使用__class__取值, 定义过滤器
@register.filter(name='object_class_name')
def object_class_name(value):
    return value.__class__.__name__
