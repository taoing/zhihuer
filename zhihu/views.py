from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.http import HttpResponse

from .models import Question, Answer, Topic, UserFollowAnswer
from zhihuer import settings
from helper.paginator_helper import paginator_helper
from user.views import User

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

    # 问题的回答, 点赞数排序
    question_answers = Answer.objects.filter(question=question).annotate(follow_nums=Count('userfollowanswer')).annotate(\
        comment_nums=Count('answercomment')).order_by('-follow_nums')

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
    topic = Topic.objects.get(pk=topic_id)
    # 话题下最新讨论(回答)
    topic_answers = Answer.objects.filter(question__in=topic.question_set.all()).annotate(follow_nums\
        =Count('userfollowanswer', distince=True)).annotate(comment_nums=Count('answercomment', distinct=True)).order_by('-pub_time')

    # 话题下回答问题的最活跃回答者, 按用户的回答赞同数排序
    # 用distinct去除重复的user_id, 但mysql数据库不支持, 使用set类型集合
    # 该话题下, 有回答的用户ID列表
    user_ids = set()
    for answer in topic_answers:
        user_ids.add(answer.author_id)
    # 最活跃用户取前5
    most_active_users = User.objects.filter(id__in=user_ids)\
        .annotate(follow_nums=Count('userfollowanswer',distinct=True), answer_nums=Count('answer', distinct=True)).order_by('-follow_nums')[:5]


    page = paginator_helper(request, topic_answers, per_page=settings.ANSWER_PER_PAGE)

    context = {}
    context['topic'] = topic
    context['most_active_users'] = most_active_users
    context['page'] = page
    return render(request, 'zhihu/topic_detail.html', context)

def add_follow_answer(request):
    '''赞同答案'''
    if request.method == 'POST':
        answer_id = int(request.POST.get('id'))
        try:
            answer = Answer.objects.get(id=answer_id)
            answer_follow_exist = UserFollowAnswer.objects.filter(user=request.user, answer=answer).first()
            if answer_follow_exist:
                answer_follow_exist.delete()
                return HttpResponse('{"status":"success", "message":"收藏"}', content_type='application/json')
            else:
                answer_follow = UserFollowAnswer(user=request.user, answer=answer)
                answer.save()
                return HttpResponse('{"status":"success", "message":"已收藏"}', content_type='application/json')
        except Exception as e:
            return HttpResponse('{"status":"fail", "message":"发生错误"}', content_type='application/json')
