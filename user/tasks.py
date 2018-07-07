# tasks.py模块要放在已注册应用的目录下

from celery.decorators import task

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from django.conf import settings

# 如果发送邮件出错， 等10s再次发送， 最多重试3次
# 修改发送邮件的方法，celery将任务放在redis中会序列化对象, 对象不能直接序列化，发送邮件的参数最好直接传值，不要传对象过来
@task(bind=True, max_retries=3, default_retry_delay=10)
def send_email(self, subject, template, to, **kwargs):
    '''发送邮件'''
    try:
        text_content = render_to_string(template+'.txt', kwargs)
        html_content = render_to_string(template+'.html', kwargs)
        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, [to])
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
    except Exception as e:
        raise self.retry(exc=e)

"""
第二种方法
from zhihuer import celery_app

@celery_app.task
def send_email(subject, template, to, **kwargs):
    '''发送邮件'''
    text_content = render_to_string(template+'.txt', kwargs)
    html_content = render_to_string(template+'.html', kwargs)
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
"""