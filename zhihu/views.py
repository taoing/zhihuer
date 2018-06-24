from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required

from .models import Question, Answer, Topic, UserFollowAnswer, AnswerComment, UserFollowQuestion, UserCollectAnswer
from zhihuer import settings
from helper.paginator_helper import paginator_helper
from user.views import User
from .forms import CommentForm

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
    context['has_follow_question'] = has_follow_question
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
    topic = Topic.objects.get(pk=topic_id)

    has_follow_topic = False
    if request.user.is_authenticated:
        if topic in request.user.topic_set.all():
            has_follow_topic = True
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
    context['has_follow_topic'] = has_follow_topic
    context['most_active_users'] = most_active_users
    context['page'] = page
    return render(request, 'zhihu/topic_detail.html', context)

@login_required
def add_follow_answer(request, answer_id):
    '''赞同答案'''
    # if request.method == 'POST':
    try:
        answer = get_object_or_404(Answer, id=answer_id)
        answer_follow_existed = UserFollowAnswer.objects.filter(user=request.user, answer=answer).first()
        if answer_follow_existed:
            answer_follow_existed.delete()
            return JsonResponse({"status":"success"})
        else:
            answer_follow = UserFollowAnswer(user=request.user, answer=answer)
            answer_follow.save()
            return JsonResponse({"status":"success"})
    except Exception as e:
        return JsonResponse({"status":"fail", "message":"发生错误"})

@login_required
def cancel_follow_answer(request, answer_id):
    '''取消赞同'''
    # if request.method == 'POST':
    try:
        answer = get_object_or_404(Answer, id=answer_id)
        answer_follow_existed = UserFollowAnswer.objects.filter(user=request.user, answer=answer).first()
        if answer_follow_existed:
            answer_follow_existed.delete()
            return JsonResponse({'status':'success'})
        else:
            return JsonResponse({'status':'nothing'})
    except Exception as e:
        print(e)
        return JsonResponse({'status':'fail', 'message':'发生错误'})

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
            return JsonResponse({'status':'success'})
        else:
            return JsonResponse({'status':'fail', 'message':'评论不能为空'})

@login_required
def follow_question(request, question_id):
    '''关注问题'''
    try:
        question = get_object_or_404(Question, id=question_id)
        follow_question_existed = UserFollowQuestion.objects.filter(user=request.user, question=question).first()
        if follow_question_existed:
            follow_question_existed.delete()
            return JsonResponse({'status':'success', 'message':'关注问题'})
        else:
            follow_question = UserFollowQuestion(user=request.user, question=question)
            follow_question.save()
            return JsonResponse({'status':'success', 'message':'已关注'})
    except Exception as e:
        return JsonResponse({'status':'fail', 'message':'发生错误'})

@login_required
def collect_answer(request, answer_id):
    '''收藏答案'''
    try:
        answer = get_object_or_404(Answer, id=answer_id)
        collect_answer_existed = UserCollectAnswer.objects.filter(user=request.user, answer=answer).first()
        if collect_answer_existed:
            collect_answer_existed.delete()
            return JsonResponse({'status':'success', 'message':'收藏'})
        else:
            collect_answer = UserCollectAnswer(user=request.user, answer=answer)
            collect_answer.save()
            return JsonResponse({'status':'success', 'message':'已收藏'})
    except Exception as e:
        return JsonResponse({'status':'fail', 'message':'发生错误'})

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