from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings

from .models import Question, Answer, Topic, UserFollowAnswer, AnswerComment, UserFollowQuestion, UserCollectAnswer
from helper.paginator_helper import paginator_helper
from user.views import User
from .forms import CommentForm, AskQuestionForm, AnswerForm

def index(request):
    '''首页'''
    all_answers = Answer.objects.annotate(comment_nums=Count('answercomment', distinct=True))\
        .annotate(follow_nums=Count('userfollowanswer', distinct=True)).order_by('-pub_time')

    # 分页
    page = paginator_helper(request, all_answers, per_page=settings.ANSWER_PER_PAGE)

    context = {}
    context['page'] = page
    return render(request, 'zhihu/index.html', context)

def question_detail(request, question_id):
    '''问题详情'''
    question = get_object_or_404(Question, pk=question_id)
    # get请求一次, 浏览量+1
    question.read_nums += 1
    question.save()

    has_follow_question = False
    if request.user.is_authenticated:
        if UserFollowQuestion.objects.filter(user=request.user, question=question):
            has_follow_question = True

    # 问题的回答
    question_answers = Answer.objects.filter(question=question).annotate(follow_nums=Count('userfollowanswer', distinct=True)).annotate(\
        comment_nums=Count('answercomment', distinct=True))

    # 问题下回答排序
    sort_type = request.GET.get('sort_type', '')
    # 如果按时间排序
    if sort_type == 'time':
        question_answers = question_answers.order_by('-pub_time')
    # 默认排序, 按点赞数数排序
    else:
        question_answers = question_answers.order_by('-follow_nums')

    # 分页
    page = paginator_helper(request, question_answers, per_page=settings.ANSWER_PER_PAGE)

    # question归属话题, 取第一个话题
    question_topic = question.topics.all().first()
    # 话题相关question, 取前5个
    relate_questions = question_topic.question_set.all().order_by('-read_nums')[:5]

    context = {}
    context['question'] = question
    context['has_follow_question'] = has_follow_question
    context['sort_type'] = sort_type
    context['page'] = page
    context['relate_questions'] = relate_questions
    return render(request, 'zhihu/question_detail.html', context)

def answer_detail(request, answer_id):
    '''回答详情'''
    answer = get_object_or_404(Answer, pk=answer_id)
    question = answer.question

    has_follow_question = False
    has_collect_answer = False
    if request.user.is_authenticated:
        if UserFollowQuestion.objects.filter(user=request.user, question=question):
            has_follow_question = True
        if UserCollectAnswer.objects.filter(user=request.user, answer=answer):
            has_collect_answer = True


    # 归属问题话题的相关问题, 按阅读量排序
    # 回答归属question归属话题, 取第一个话题
    question_topic = question.topics.all().first()
    # 话题相关question, 取前5个
    relate_questions = question_topic.question_set.all().order_by('-read_nums')[:5]
    # 评论表单
    comment_form = CommentForm()
    # 评论分页
    answer_comments = answer.answercomment_set.all().order_by('-add_time')
    page = paginator_helper(request, answer_comments, per_page=settings.COMMENT_PER_PAGE)

    context = {}
    context['answer'] = answer
    context['has_follow_question'] = has_follow_question
    context['has_collect_answer'] = has_collect_answer
    context['relate_questions'] = relate_questions
    context['comment_form'] = comment_form
    context['page'] = page
    return render(request, 'zhihu/answer_detail.html', context)

def explore(request):
    '''发现页'''
    # 按浏览量取前5个
    recommend_questions = Question.objects.all().order_by('-read_nums')[:5]

    # 本月推荐: 回答在本月有用户最多的点赞或收藏
    today = datetime.today()
    recommend_answer_month = Answer.objects.all().filter(pub_time__year=today.year, pub_time__month=\
        today.month).annotate(follow_nums=Count('userfollowanswer')).order_by('-follow_nums')

    page_month = paginator_helper(request, recommend_answer_month, per_page=settings.ANSWER_PER_PAGE)

    # 今日推荐: 回答在今日有用户最多的点赞或收藏
    recommend_answer_today = Answer.objects.all().filter(pub_time__year=today.year, pub_time__month=\
        today.month, pub_time__day=today.day).annotate(follow_nums=Count('userfollowanswer')).order_by('-follow_nums')

    page_today = paginator_helper(request, recommend_answer_today, per_page=settings.ANSWER_PER_PAGE)

    # 热门话题, 问题最多的话题
    hot_topics = Topic.objects.all().annotate(question_nums=Count('question')).order_by('-question_nums')[:5]

    context = {}
    context['recommend_questions'] = recommend_questions
    context['page_month'] = page_month
    context['page_today'] = page_today
    context['hot_topics'] = hot_topics

    return render(request, 'zhihu/explore.html', context)

def topic_list(request):
    '''话题广场'''
    # 话题根据关注用户的数量排序
    all_topics = Topic.objects.all().order_by('add_time')
    # 热门话题, 关注者最多的话题
    hot_topics = Topic.objects.all().annotate(user_nums=Count('users')).order_by('-user_nums')[:5]
    page = paginator_helper(request, all_topics, per_page = settings.TOPIC_PER_PAGE)

    context = {}
    context['page'] = page
    context['hot_topics'] = hot_topics

    return render(request, 'zhihu/topic_list.html', context)

def topic_detail(request, topic_id):
    '''话题详情'''
    topic = get_object_or_404(Topic, id=topic_id)
    context = {}
    has_follow_topic = False
    if request.user.is_authenticated:
        if topic in request.user.topic_set.all():
            has_follow_topic = True

    # 话题下回答
    topic_answers = Answer.objects.filter(question__in=topic.question_set.all()).annotate(follow_nums\
        =Count('userfollowanswer', distinct=True)).annotate(comment_nums=Count('answercomment', distinct=True))

    # 话题下回答问题的最活跃回答者, 按用户的回答数排序
    # 用distinct去除重复的user_id, 但mysql数据库不支持, 使用set类型集合去除重复的user_id
    # 该话题下, 有回答的用户ID列表
    user_ids = set()
    for answer in topic_answers:
        user_ids.add(answer.author_id)

    # 所有用户在话题下的回答数列表
    user_answer_nums_list = []
    for user_id  in user_ids:
        user_answer_nums = topic_answers.filter(author_id=user_id).count()
        user_answer_nums_list.append({'user_id':user_id, 'user_answer_nums':user_answer_nums})

    # 依据回答数排序, 排序函数sorted的key参数
    def get_nums(obj):
        return obj['user_answer_nums']
    
    user_answer_nums_list_sorted = sorted(user_answer_nums_list, key=get_nums, reverse=True)
    # 最活跃用户取前3
    most_active_users = []
    for obj in user_answer_nums_list_sorted[:3]:
        user = User.objects.get(id=obj['user_id'])
        # 用户话题回答数
        user.topic_answer_nums = obj['user_answer_nums']
        # 用户话题下回答赞同数
        user.topic_answer_follow_nums = UserFollowAnswer.objects.filter(answer__author=user, answer__in=topic_answers).count()
        most_active_users.append(user)

    topic_type = request.GET.get('topic_type', '')
    # 话题下回答排序, 默认按时间排序
    if topic_type == 'wonderful':
        # 获取话题下精彩回答, 按点赞数排序
        topic_answers = topic_answers.order_by('-follow_nums')
    else:
        topic_answers = topic_answers.order_by('-pub_time')

    page = paginator_helper(request, topic_answers, per_page=settings.ANSWER_PER_PAGE)

    context['topic'] = topic
    context['has_follow_topic'] = has_follow_topic
    context['most_active_users'] = most_active_users
    context['topic_type'] = topic_type
    context['page'] = page
    return render(request, 'zhihu/topic_detail.html', context)

def topic_question(request, topic_id):
    '''话题下等待回答问题, 按时间排序'''
    topic = get_object_or_404(Topic, id=topic_id)
    context = {}
    has_follow_topic = False
    if request.user.is_authenticated:
        if topic in request.user.topic_set.all():
            has_follow_topic = True

    topic_questions = topic.question_set.all().order_by('-pub_time')

    topic_questions_page = paginator_helper(request, topic_questions, per_page = settings.QUESTION_PER_PAGE)

    context['topic'] = topic
    context['topic_questions_page'] = topic_questions_page
    return render(request, 'zhihu/topic_question.html', context)

def topic_answerer(request, topic_id):
    '''话题下活跃回答者'''
    topic = get_object_or_404(Topic, id=topic_id)
    has_follow_topic = False
    if request.user.is_authenticated:
        if topic in request.user.topic_set.all():
            has_follow_topic = True

    topic_answers = Answer.objects.filter(question__in=topic.question_set.all())
    user_list = set()
    for answer in topic_answers:
        user_list.add(answer.author)
    # 用户话题下回答列表
    user_answer_nums_list = []
    for user in user_list:
        # 用户在话题下的回答
        user_answers = topic_answers.filter(author=user)
        # 用户在话题下的回答数
        user.user_answer_nums = user_answers.count()
        # 用户在话题下的回答赞同数
        user.user_answer_follow_nums = UserFollowAnswer.objects.filter(answer__in=user_answers).count()
        user_answer_nums_list.append(user)

    def get_nums(obj):
        return obj.user_answer_nums
    user_answer_nums_list_sorted = sorted(user_answer_nums_list, key=get_nums, reverse=True)
    page = paginator_helper(request, user_answer_nums_list_sorted, settings.USER_PER_PAGE)

    context = {}
    context['topic'] = topic
    context['has_follow_topic'] = has_follow_topic
    context['page'] = page
    return render(request, 'zhihu/topic_answerer.html', context)

@login_required
def add_follow_answer(request):
    '''赞同回答'''
    answer_id = int(request.GET.get('answer_id', ''))
    answer = get_object_or_404(Answer, id=answer_id)
    answer_follow_existed = UserFollowAnswer.objects.filter(user=request.user, answer=answer)
    print(answer_follow_existed.count())
    if answer_follow_existed:
        answer_follow_existed.delete()
        return JsonResponse({'status':'success', 'reason':'cancel'})
    else:
        answer_follow = UserFollowAnswer(user=request.user, answer=answer)
        answer_follow.save()
        return JsonResponse({'status':'success', 'reason':'add'})

@login_required
def cancel_follow_answer(request):
    '''取消赞同'''
    answer_id = int(request.GET.get('answer_id', ''))
    answer = get_object_or_404(Answer, id=answer_id)
    answer_follow_existed = UserFollowAnswer.objects.filter(user=request.user, answer=answer)
    if answer_follow_existed:
        answer_follow_existed.delete()
        return JsonResponse({'status':'success', 'reason':'cancel'})
    else:
        return JsonResponse({'status':'success', 'reason':'nothing'})

@login_required
def comment_answer(request, answer_id):
    '''评论回答'''
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.cleaned_data.get('comment')
            answer = get_object_or_404(Answer, id=answer_id)
            answer_comment = AnswerComment(user=request.user, answer=answer, comment=comment)
            answer_comment.save()
            return JsonResponse({'status':'success', 'message':'你的评论已提交'})
        else:
            return JsonResponse({'status':'fail', 'message':'评论不能为空'})

@login_required
def follow_question(request):
    '''关注问题'''
    question_id = int(request.GET.get('question_id', ''))
    question = get_object_or_404(Question, id=question_id)
    follow_question_existed = UserFollowQuestion.objects.filter(user=request.user, question=question)
    if follow_question_existed:
        follow_question_existed.delete()
        return JsonResponse({'status':'success', 'message':'关注问题'})
    else:
        follow_question = UserFollowQuestion(user=request.user, question=question)
        follow_question.save()
        return JsonResponse({'status':'success', 'message':'已关注'})

@login_required
def collect_answer(request):
    '''收藏答案'''
    answer_id = int(request.GET.get('answer_id', ''))
    answer = get_object_or_404(Answer, id=answer_id)
    collect_answer_existed = UserCollectAnswer.objects.filter(user=request.user, answer=answer)
    if collect_answer_existed:
        collect_answer_existed.delete()
        return JsonResponse({'status':'success', 'message':'收藏'})
    else:
        collect_answer = UserCollectAnswer(user=request.user, answer=answer)
        collect_answer.save()
        return JsonResponse({'status':'success', 'message':'已收藏'})

@login_required
def follow_topic(request, topic_id):
    '''关注问题'''
    try:
        topic = get_object_or_404(Topic, id=topic_id)
        if topic in request.user.topic_set.all():
            request.user.topic_set.remove(topic)
            return JsonResponse({'status':'success', 'message':'关注话题'})
        else:
            request.user.topic_set.add(topic)
            return JsonResponse({'status':'success', 'message':'已关注'})
    except Exception as e:
        return JsonResponse({'status':'fail', 'message':'发生错误'})

@login_required
def ask_question(request):
    '''提问'''
    ask_quesiton_form = AskQuestionForm()

    if request.method == 'POST':
        ask_quesiton_form = AskQuestionForm(request.POST)
        if ask_quesiton_form.is_valid():
            question = Question()
            question.author = request.user
            question.title = ask_quesiton_form.cleaned_data.get('title')
            question.content = ask_quesiton_form.cleaned_data.get('content')
            question.is_anonymous = ask_quesiton_form.cleaned_data.get('anonymous')
            question.save()
            # 保存多对多关系前保存question对象
            question.topics.set(ask_quesiton_form.cleaned_data.get('topics'))
            messages.info(request, '你的问题已提交')
            return redirect(reverse('question_detail', args=(question.id,)))
        messages.info(request, '你的输入有误')

    context = {}
    context['ask_question_form'] = ask_quesiton_form
    return render(request, 'zhihu/ask_question.html', context)

def question_list(request):
    '''回答-问题列表'''
    questions = Question.objects.all().order_by('-pub_time').annotate(answer_nums=Count('answer', distinct=True), follow_nums=Count('userfollowquestion', distinct=True))
    hot_questions = Question.objects.all().annotate(answer_nums=Count('answer', distinct=True), follow_nums=Count('userfollowquestion', distinct=True)).order_by('-follow_nums')
    
    #分页
    questions_page = paginator_helper(request, questions, per_page=settings.QUESTION_PER_PAGE)
    hot_questions_page = paginator_helper(request, hot_questions, per_page = settings.QUESTION_PER_PAGE)

    context = {}
    context['questions_page'] = questions_page
    context['hot_questions_page'] = hot_questions_page
    return render(request, 'zhihu/question_list.html', context)

@login_required
def answer_question(request, question_id):
    '''回答问题'''
    answer_form = AnswerForm()
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        answer_form = AnswerForm(request.POST)
        if answer_form.is_valid():
            answer = Answer()
            answer.question = question
            answer.author = request.user
            answer.content = answer_form.cleaned_data.get('content')
            answer.is_anonymous = answer_form.cleaned_data.get('anonymous')
            answer.save()
            messages.info(request, '你的回答已提交')
            return redirect(reverse('question_detail', args=(question.id,)))

    context = {}
    context['question'] = question
    context['answer_form'] = answer_form
    return render(request, 'zhihu/answer_question.html', context)