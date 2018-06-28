from django.shortcuts import render, redirect, get_object_or_404

from itertools import chain
from datetime import datetime, timedelta
import random

from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.backends import ModelBackend #这是默认用户认证后端
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required

from .models import User, CheckCode
from zhihu.models import Answer, Question, Topic
from .forms import RegisterForm, LoginForm, ForgetPwdForm, UserProfileForm, ChangePasswordForm, ChangeEmailForm
from helper.send_email import send_email
from helper.paginator_helper import paginator_helper

class CustomModelBackend(ModelBackend):
    '''自定认证后端类, 重写ModelBackend的authenticate方法, 可以使用username和email同时登录'''
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 使用Q对象进行数据库or查询
        try:
            user = User.objects.get(Q(username=username)|Q(email=username))
            # 验证明文密码
            if user.check_password(password) and user.is_active:
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
            user.nickname = register_form.cleaned_data.get('username')
            user.email = register_form.cleaned_data.get('email')
            user.set_password(register_form.cleaned_data.get('password'))
            user.save()

            # 生成账户确认签名
            token = user.generate_confirm_token()
            # 发送账户激活链接邮件
            send_email('知乎儿账户确认', 'user/email/user_confirm', user.email, user=user, token=token)
            # 网页显示账户注册成功消息
            messages.info(request, '账户已注册, 一封账户确认邮件已发往你的邮箱, 请查收')
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
            if user:
                login(request, user)
                # 登录成功后跳转到上一个界面
                # 检查提交表单的next值
                redirect_next = request.POST.get('next')
                if redirect_next:
                    return redirect(redirect_next)
                return redirect(reverse('index'))
            else:
                messages.info(request, '用户名或密码错误')

    context = {}
    context['login_form'] = login_form
    return render(request, 'user/login.html', context)

def user_logout(request):
    '''退出登录'''
    logout(request)
    return redirect(reverse('index'))

def user_confirm(request, token):
    '''确认账户'''
    if request.user.confirmed:
        return redirect(reverse('index'))
    if request.user.confirm(token):
        messages.info(request, '你的账户已确认成功')
        return redirect(reverse('index'))
    else:
        messages.info(request, '确认链接无效或过期')
        return redirect(reverse('index'))

def resend_confirm_email(request):
    '''重新发送确认链接'''
    user = request.user
    token = user.generate_confirm_token()
    send_email('知乎儿账户确认', 'user/email/user_confirm', user.email, user=user, token=token)
    messages.info(request, '确认邮件已发送')
    return redirect(reverse('index'))

def get_time(obj):
    '''返回对象的创建时间, 在sorted中以对象的创建时间比较'''
    if isinstance(obj, Answer) or isinstance(obj, Question):
        return obj.pub_time
    else:
        return obj.add_time

def user_home(request, user_id):
    '''用户主页'''
    user = get_object_or_404(User, id=user_id)

    user_answers = user.answer_set.all()
    user_questions = user.question_set.all()
    user_follow_answers = user.userfollowanswer_set.all()
    user_collect_answers = user.usercollectanswer_set.all()
    user_follow_questions = user.userfollowquestion_set.all()
    # 使用itertools.chain合并多个queryset, 反应用户的动态
    user_trend = chain(user_answers, user_questions, user_follow_answers, user_collect_answers, user_follow_questions)
    user_trend_sorted = sorted(user_trend, key=get_time, reverse=True)
    # 分页
    user_trend_sorted_page = paginator_helper(request, user_trend_sorted, per_page=settings.TREND_PER_PAGE)

    context = {}
    context['user'] = user
    context['user_trend_sorted_page'] = user_trend_sorted_page
    return render(request, 'user/user_home.html', context)

def user_answer(request, user_id):
    '''用户主页--回答'''
    user = get_object_or_404(User, id=user_id)
    user_answers = user.answer_set.all()

    user_answers_page = paginator_helper(request, user_answers, per_page=settings.ANSWER_PER_PAGE)
    context = {}
    context['user'] = user
    context['user_answers_page'] = user_answers_page
    return render(request, 'user/user_answer.html', context)

def user_question(request, user_id):
    '''用户主页--提问'''
    user = get_object_or_404(User, id=user_id)
    user_questions = user.question_set.all()

    user_questions_page = paginator_helper(request, user_questions, per_page=settings.QUESTION_PER_PAGE)
    context = {}
    context['user'] = user
    context['user_questions_page'] = user_questions_page
    return render(request, 'user/user_question.html', context)

def user_collect_answer(request, user_id):
    '''用户主页--收藏的回答'''
    user = get_object_or_404(User, id=user_id)
    user_collect_answers = user.usercollectanswer_set.all().order_by('-add_time')
    # 取出answer对象
    user_collect_answers = [obj.answer for obj in user_collect_answers]
    user_collect_answers_page = paginator_helper(request, user_collect_answers, per_page=settings.ANSWER_PER_PAGE)
    context = {}
    context['user'] = user
    context['user_collect_answers_page'] = user_collect_answers_page
    return render(request, 'user/user_collect_answer.html', context)

def user_follow_topic(request, user_id):
    '''用户主页--关注话题'''
    user = get_object_or_404(User, id=user_id)
    # 用户关注的话题
    user_topics = user.topic_set.all()
    user_topics_list = []
    if user_topics:
        for topic in user_topics:
            # 话题下所有问题
            topic_questions = topic.question_set.all()
            # 用户在该话题下的所有回答
            user_answer_nums = Answer.objects.filter(question__in=topic_questions, author=user).count()
            # 创建dict对象放入列表中
            user_topics_list.append({'topic':topic, 'user_answer_nums':user_answer_nums})

    user_topics_page = paginator_helper(request, user_topics_list, per_page=settings.TOPIC_PER_PAGE)
    context = {}
    context['user'] = user
    context['user_topics_page'] = user_topics_page
    return render(request, 'user/user_follow_topic.html', context)

def user_follow_question(request, user_id):
    '''用户主页--关注问题'''
    user = get_object_or_404(User, id=user_id)
    # 用户关注问题
    user_follow_questions = user.userfollowquestion_set.all()
    # 取出question对象
    user_follow_questions = [obj.question for obj in user_follow_questions]
    user_follow_questions_page = paginator_helper(request, user_follow_questions, per_page=settings.QUESTION_PER_PAGE)
    context = {}
    context['user'] = user
    context['user_follow_questions_page'] = user_follow_questions_page
    return render(request, 'user/user_follow_question.html', context)

def user_follow_user(request, user_id):
    '''用户主页--用户关注'''
    user = get_object_or_404(User, id=user_id)
    # 该用户关注的用户
    to_users = user.to_user_set.all().order_by('-add_time')
    # 取出关注的用户
    to_users = [obj.to_user for obj in to_users]
    to_users_page = paginator_helper(request, to_users, per_page = settings.USER_PER_PAGE)
    context = {}
    context['user'] = user
    context['to_users_page'] = to_users_page
    return render(request, 'user/user_follow_user.html', context)

def user_followed_by_user(request, user_id):
    '''用户主页--用户关注者'''
    user = get_object_or_404(User, id=user_id)
    # 关注该用户的用户
    from_users = user.from_user_set.all().order_by('-add_time')
    # 取出关注者
    from_users = [obj.from_user for obj in from_users]
    from_users_page = paginator_helper(request, from_users, per_page=settings.USER_PER_PAGE)
    context = {}
    context['user'] = user
    context['from_users_page'] = from_users_page
    return render(request, 'user/user_followed_user.html', context)

def user_topic_answer(request, user_id, topic_id):
    '''用户在话题下的回答'''
    user = get_object_or_404(User, id=user_id)
    try:
        topic = user.topic_set.get(id=topic_id)
    except Exception as e:
        return redirect(reverse('index'))
    topic_questions = topic.question_set.all()
    topic_answers = Answer.objects.filter(question__in=topic_questions, author=user)
    topic_answers_page = paginator_helper(request, topic_answers, per_page=settings.ANSWER_PER_PAGE)
    context = {}
    context['user'] = user
    context['topic'] = topic
    context['topic_answers_page'] = topic_answers_page
    return render(request, 'user/user_topic_answer.html', context)

def reset_password(request):
    '''忘记密码, 找回密码'''
    if not request.user.is_anonymous:
        return redirect(reverse('index'))
    if request.method == 'POST':
        form = ForgetPwdForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password_2 = form.cleaned_data.get('password_2')
            user = User.objects.get(email=email)
            user.set_password(password_2)
            user.save()

            # 完成验证后删除验证码
            user_check_code = CheckCode.objects.filter(user=user)
            if user_check_code.count() > 0:
                user_check_code.delete()

            # 重置密码后需要重新登录
            messages.info(request, '密码已重置, 现在可以登录')
            return redirect(reverse('user_login'))
    else:
        form = ForgetPwdForm()
    context = {}
    context['form'] = form
    return render(request, 'user/reset_password.html', context)

def get_check_code(request):
    '''发送验证码'''
    if not request.user.is_anonymous:
        return redirect(reverse('index'))

    email = request.GET.get('email', '')
    # 随机生成验证码
    alist = ['0','1','2','3','4','5','6','7','8','9']
    # 根据ascii码将数字转换为大写字母
    for i in range(65,91):
        alist.append(chr(i))

    # 打乱alist的顺序
    random.shuffle(alist)

    code_list = random.sample(alist, 6)
    check_code = ''.join(code_list)

    data = {}
    try:
        user = User.objects.filter(email=email)
        if user.count() == 0:
            data['status'] = 'fail'
            data['message'] = '该邮箱还没有注册'
            return JsonResponse(data)

        user = user.first()
        # 检查是否短时间 1分钟 内已发送过验证码
        user_check_code = CheckCode.objects.filter(user=user)
        if user_check_code.count() > 0:
            user_check_code = user_check_code.first()
            if datetime.now() < user_check_code.add_time + timedelta(seconds=60):
                data['status'] = 'fail'
                data['message'] = '1分钟内已发送过验证码, 请检查邮箱'
                return JsonResponse(data)
        else:
            user_check_code = CheckCode(user=user)

        user_check_code.check_code = check_code
        user_check_code.save()
        # 发送邮件
        send_email('知乎儿验证码', 'user/email/reset_password', email, user_check_code=user_check_code)
        return JsonResponse({'status':'success'})
    except Exception as e:
        pass

@login_required
def edit_profile(request):
    '''修改个人资料'''
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.info(request, '你的资料已更新')
            return render(request, 'user/edit_profile.html')
    return render(request, 'user/edit_profile.html')

@login_required
def update_image(request):
    '''修改头像'''
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            request.user.image = image
            request.user.save()
            messages.info(request, '你的头像已修改')
            return render(request, 'user/edit_profile.html')
        else:
            return render(request, 'user/edit_profile.html')

@login_required
def change_password(request):
    '''修改密码'''
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, request=request)
        if form.is_valid():
            password_2 = form.cleaned_data.get('password_2')
            request.user.set_password(password_2)
            request.user.save()
            logout(request)
            messages.info(request, '你的密码已修改, 请重新登录')
            return redirect(reverse('user_login'))
    else:
        form = ChangePasswordForm(request=request)
    context = {}
    context['form'] = form
    return render(request, 'user/change_password.html', context)

@login_required
def change_email_request(request):
    '''请求修改邮箱, 发送修改邮箱链接'''
    if request.method == 'POST':
        form = ChangeEmailForm(request.POST, request=request)
        if form.is_valid():
            password = form.cleaned_data.get('password')
            new_email = form.cleaned_data.get('new_email')
            if request.user.check_password(password):
                token = request.user.generate_change_email_token(new_email)
                send_email('知乎儿修改邮箱', 'user/email/change_email', new_email, token=token)
                messages.info(request, '一封含有确认修改邮箱链接的邮件已发送到你的新邮箱, 请查收')
                return redirect(reverse('index'))
            else:
                messages.info(request, '密码错误')
    else:
        form = ChangeEmailForm(request=request)
    context = {}
    context['form'] = form
    return render(request, 'user/change_email.html', context)

def change_email(request, token):
    '''确认修改邮箱'''
    if request.user.confirm_change_email(token):
        messages.info(request, '你的邮箱已经修改')
    else:
        messages.info(request, '错误请求')
    return redirect(reverse('index'))