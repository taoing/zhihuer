from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.db.models import Count

from .models import Question, Answer, Topic
from zhihuer import settings
from helper.paginator_helper import paginator_helper

def index(request):
    '''首页'''
    all_answers = Answer.objects.all().order_by('-pub_time')

    # 分页
    page = paginator_helper(request, all_answers, per_page=settings.ANSWER_PER_PAGE)

    context = {}
    context['page'] = page
    return render(request, 'zhihu/index.html', context)

def question_detail(request, question_id):
    '''问题详情'''
    question = get_object_or_404(Question, pk=question_id)

    # 问题的回答
    question_answers = Answer.objects.filter(question=question).annotate(follow_nums=Count('userfollowanswer')).order_by('-follow_nums')

    # 分页
    page = paginator_helper(request, question_answers, per_page=settings.ANSWER_PER_PAGE)

    # question归属话题, 取第一个话题
    question_topic = question.topics.all().first()
    # 话题相关question, 取前5个
    relate_questions = question_topic.question_set.all().order_by('-read_nums')[:5]

    context = {}
    context['question'] = question
    context['page'] = page
    context['relate_questions'] = relate_questions
    return render(request, 'zhihu/question_detail.html', context)

def answer_detail(request, answer_id):
    '''回答详情'''
    answer = get_object_or_404(Answer, pk=answer_id)

    # 归属问题话题的相关问题, 按点赞数和收藏数之和排序
    # 回答归属question归属话题, 取第一个话题
    question_topic = answer.question.topics.all().first()
    # 话题相关question, 取前5个
    relate_questions = question_topic.question_set.all().order_by('-read_nums')[:5]

    # 回答评论
    pass
    # 评论分页
    pass

    context = {}
    context['answer'] = answer
    context['relate_questions'] = relate_questions
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