# -*- coding: utf-8 -*-

from threading import Thread

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_email_async(msg):
    '''新线程发送邮件'''
    msg.send()


def send_email(subject, template, to, request, **kwargs):
    '''发送邮件'''
    text_content = render_to_string(template + '.txt', kwargs, request=request)
    html_content = render_to_string(template + '.html', kwargs, request=request)
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM,
                                 [to])
    msg.attach_alternative(html_content, 'text/html')
    # 发送邮件是耗时操作, 创建新线程执行实际的发送任务, 不会阻塞
    t = Thread(target=send_email_async, args=(msg,))
    t.start()
    return t
