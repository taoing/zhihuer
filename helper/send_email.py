# -*- coding: utf-8 -*-

from threading import Thread
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from zhihuer.settings import EMAIL_FROM

def send_email_async(msg):
    '''新线程发送邮件'''
    msg.send()

def send_email(subject, template, to, **kwargs):
    '''发送邮件'''
    text_content = render_to_string(template+'.txt', kwargs)
    html_content = render_to_string(template+'.html', kwargs)
    msg = EmailMultiAlternatives(subject, text_content, EMAIL_FROM, [to])
    msg.attach_alternative(html_content, 'text/html')
    # 发送邮件是耗时操作, 创建新线程执行实际的发送任务, 不会阻塞
    t = Thread(target=send_email_async, args=(msg,))
    t.start()
    return t