from datetime import datetime, timedelta

import jieba #中文分词

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings

#cache
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.cache import get_cache_key

from .models import Question, Answer, Topic, UserFollowAnswer, AnswerComment, UserFollowQuestion, UserCollectAnswer
from helper.paginator_helper import paginator_helper
from user.models import User
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
    question_answers = cache.get('question_answers'+str(question_id))
    if not question_answers:
        question_answers = Answer.objects.filter(question=question).annotate(follow_nums=Count('userfollowanswer', distinct=True)).annotate(\
            comment_nums=Count('answercomment', distinct=True))
        cache.set('question_answers'+str(question_id), question_answers, 5*60)

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
    # 话题相关question, 取前5个, 并排除自身
    relate_questions = cache.get('relate_questions'+str(question_id))
    if not relate_questions:
        relate_questions = question_topic.question_set.exclude(id=question_id).order_by('-read_nums')[:5]
        cache.set('relate_questions'+str(question_id), relate_questions, 5*60)

    context = {}
    context['question'] = question
    context['has_follow_question'] = has_follow_question
    context['sort_type'] = sort_type
    context['page'] = page
    context['relate_questions'] = relate_questions
    return render(request, 'zhihu/question_detail.html', context)

@cache_page(5*60, key_prefix='follow_question_user')
def follow_question_user(request, question_id):
    '''关注问题的用户'''
    question = get_object_or_404(Question, id=question_id)
    if question.get_follow_nums() == 0:
        return redirect(reverse('question_detail', args=(question_id,)))

    # 获取question关注记录, obj.user的方式获取记录中的user对象
    follow_question_users = question.userfollowquestion_set.order_by('-add_time')

    follow_question_users_page = paginator_helper(request, follow_question_users, per_page=settings.USER_PER_PAGE)
    context = {}
    context['question'] = question
    context['follow_question_users_page'] = follow_question_users_page
    return render(request, 'zhihu/follow_question_user.html', context)

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
    # 话题相关question, 取前5个, 并排除自身
    relate_questions = cache.get('relate_questions'+str(answer_id))
    if not relate_questions:
        relate_questions = question_topic.question_set.exclude(id=answer.question_id).order_by('-read_nums')[:5]
        cache.set('relate_questions'+str(answer_id), relate_questions, 5*60)
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

# use cache
@cache_page(10*60, key_prefix='explore')
def explore(request):
    '''发现页'''
    # 按浏览量取前5个
    recommend_questions = Question.objects.all().order_by('-read_nums')[:5]
    # 排名第一的问题获取点赞最多的回答
    first_question = recommend_questions[0]
    first_question.follow_est_answer = first_question.get_follow_est_answer()
    recommend_questions_list = [first_question]
    for question in recommend_questions[1:]:
        recommend_questions_list.append(question)

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
    hot_topics = Topic.objects.annotate(question_nums=Count('question')).order_by('-question_nums')[:5]

    context = {}
    context['recommend_questions'] = recommend_questions_list
    context['page_month'] = page_month
    context['page_today'] = page_today
    context['hot_topics'] = hot_topics

    return render(request, 'zhihu/explore.html', context)

@cache_page(10*60, key_prefix='explore_recommend')
def explore_recommend(request):
    '''发现页更多推荐'''
    # 取最近3个月的问题, 按问题阅读量排序
    recommend_questions = Question.objects.filter(pub_time__gt=datetime.now()-timedelta(days=90)).order_by('-read_nums')
    # 每个问题获取点赞最多的回答
    recommend_questions_list = []
    for question in recommend_questions:
        follow_est_answer = question.get_follow_est_answer()
        # 问题至少有回答, 排除没有问答的问题
        if follow_est_answer:
            question.follow_est_answer = follow_est_answer
            recommend_questions_list.append(question)

    # 热门话题, 回答最多的话题
    # annotate聚合函数, 获取每个话题下问题的回答数
    hot_topics = Topic.objects.annotate(answer_nums=Count('question__answer')).order_by('-answer_nums')[:5]

    recommend_questions_page = paginator_helper(request, recommend_questions_list, per_page=settings.QUESTION_PER_PAGE)

    context = {}
    context['recommend_questions_page'] = recommend_questions_page
    context['hot_topics'] = hot_topics
    return render(request, 'zhihu/explore_recommend.html', context)

@cache_page(10*60, key_prefix='topic_list')
def topic_list(request):
    '''话题广场'''
    # 话题根据关注用户的数量排序
    all_topics = Topic.objects.annotate(user_nums=Count('users')).order_by('-user_nums')
    # 热门话题, 提问最多的话题
    hot_topics = Topic.objects.annotate(question_nums=Count('question')).order_by('-question_nums')[:5]
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
    topic_answers = cache.get('topic_answers'+str(topic_id))
    if not topic_answers:
        topic_answers = Answer.objects.filter(question__in=topic.question_set.all()).annotate(follow_nums\
            =Count('userfollowanswer', distinct=True)).annotate(comment_nums=Count('answercomment', distinct=True))
        cache.set('topic_answers'+str(topic_id), topic_answers, 5*60)

    '''
    # 话题下回答问题的最活跃回答者, 按用户的回答数排序
    # 用distinct去除重复的user_id, 但mysql数据库不支持, 使用set类型集合去除重复的user_id
    # 该话题下, 有回答的用户ID列表
    user_ids = cache.get('user_ids'+'_topic_'+str(topic_id))
    if not user_ids:
        user_ids = set()
        for answer in topic_answers:
            user_ids.add(answer.author_id)
        cache.set('user_ids'+'_topic_'+str(topic_id), user_ids, 5*60)

    most_active_users = cache.get('most_active_users'+str(topic_id))
    if not most_active_users:
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
        cache.set('most_active_users'+str(topic_id), most_active_users, 10*60)
    '''

    user_answer_nums_list_sorted = cache.get('user_answer_nums_list_sorted'+str(topic_id))
    if not user_answer_nums_list_sorted:
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
        # 活跃用户按回答数排序
        def get_nums(obj):
            return obj.user_answer_nums
        user_answer_nums_list_sorted = sorted(user_answer_nums_list, key=get_nums, reverse=True)
        cache.set('user_answer_nums_list_sorted'+str(topic_id), user_answer_nums_list_sorted, 10*60)
    # 最活跃用户取前3
    most_active_users = user_answer_nums_list_sorted[:3]

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

    topic_questions = cache.get('topic_questions'+str(topic_id))
    if not topic_questions:
        topic_questions = topic.question_set.all().order_by('-pub_time')
        cache.set('topic_questions'+str(topic_id), topic_questions, 10*60)

    # 话题下用户回答数排序
    user_answer_nums_list_sorted = cache.get('user_answer_nums_list_sorted'+str(topic_id))
    if not user_answer_nums_list_sorted:
        topic_answers = Answer.objects.filter(question__in=topic_questions)
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
        # 活跃用户按回答数排序
        def get_nums(obj):
            return obj.user_answer_nums
        user_answer_nums_list_sorted = sorted(user_answer_nums_list, key=get_nums, reverse=True)
        cache.set('user_answer_nums_list_sorted'+str(topic_id), user_answer_nums_list_sorted, 10*60)
    # 最活跃用户取前3
    most_active_users = user_answer_nums_list_sorted[:3]

    topic_questions_page = paginator_helper(request, topic_questions, per_page = settings.QUESTION_PER_PAGE)

    context['topic'] = topic
    context['topic_questions_page'] = topic_questions_page
    context['most_active_users'] = most_active_users
    return render(request, 'zhihu/topic_question.html', context)

def topic_answerer(request, topic_id):
    '''话题下活跃回答者'''
    topic = get_object_or_404(Topic, id=topic_id)
    has_follow_topic = False
    if request.user.is_authenticated:
        if topic in request.user.topic_set.all():
            has_follow_topic = True

    # 话题下用户回答数排序
    user_answer_nums_list_sorted = cache.get('user_answer_nums_list_sorted'+str(topic_id))
    if not user_answer_nums_list_sorted:
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
        # 活跃用户按回答数排序
        def get_nums(obj):
            return obj.user_answer_nums
        user_answer_nums_list_sorted = sorted(user_answer_nums_list, key=get_nums, reverse=True)
        cache.set('user_answer_nums_list_sorted'+str(topic_id), user_answer_nums_list_sorted, 10*60)


    page = paginator_helper(request, user_answer_nums_list_sorted, settings.USER_PER_PAGE)

    context = {}
    context['topic'] = topic
    context['has_follow_topic'] = has_follow_topic
    context['page'] = page
    return render(request, 'zhihu/topic_answerer.html', context)

def follow_topic_user(request, topic_id):
    '''关注话题的用户'''
    topic = get_object_or_404(Topic, id=topic_id)
    has_follow_topic = False
    if request.user.is_authenticated:
        if topic in request.user.topic_set.all():
            has_follow_topic = True

    topic_users_list = cache.get('topic_users_list'+str(topic_id))
    if not topic_users_list:
        # 关注话题的用户
        topic_users = topic.users.all()
        # 话题下的回答
        topic_answers = Answer.objects.filter(question__in=topic.question_set.all())

        topic_users_list = []
        for user in topic_users:
            user.answer_nums = topic_answers.filter(author=user).count()
            topic_users_list.append(user)
        cache.set('topic_users_list'+str(topic_id), topic_users_list, 10*60)

    topic_users_page = paginator_helper(request, topic_users_list, per_page=settings.USER_PER_PAGE)

    context = {}
    context['topic'] = topic
    context['has_follow_topic'] = has_follow_topic
    context['topic_users_page'] = topic_users_page
    return render(request, 'zhihu/follow_topic_user.html', context)

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

@cache_page(5*60, key_prefix='question_list')
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

@cache_page(5*60, key_prefix='search')
def search(request):
    '''简单的搜索功能, 使用数据库模糊查询, 记录较多时性能应该不好吧'''
    search_type = request.GET.get('search_type')
    keywords = request.GET.get('keywords', '')
    search_type_list = ['question', 'answer', 'topic', 'user']
    print(search_type)
    print(keywords)
    print(len(keywords))

    if not search_type:
        return redirect(reverse('index'))
    if search_type not in search_type_list:
        return redirect(reverse('index'))
    if not keywords:
        return redirect(reverse('index'))
    if len(keywords) > 20:
        return redirect(reverse('index'))

    # jieba分词(中文)
    seg_list = jieba.cut(keywords, cut_all=False) #返回generator迭代器

    if search_type == 'question':
        # Q对象
        q = Q()
        for word in seg_list:
            q = q|Q(title__icontains=word)
        search_results = Question.objects.filter(q).order_by('id')[:100]

    if search_type == 'answer':
        q = Q()
        for word in seg_list:
            q = q|Q(content__icontains=word)
        search_results = Answer.objects.filter(q).order_by('id')[:100]

    if search_type == 'topic':
        q = Q()
        for word in seg_list:
            q = q|Q(name__icontains=word)
        search_results = Topic.objects.filter(q).order_by('id')[:100]

    if search_type == 'user':
        q = Q()
        for word in seg_list:
            q = q|Q(nickname__icontains=word)|Q(username__icontains=word)
        search_results = User.objects.filter(q).order_by('id')[:100]

    search_results_page = paginator_helper(request, search_results, per_page=settings.SEARCH_PER_PAGE)

    context = {}
    context['search_type'] = search_type
    context['keywords'] = keywords
    context['search_results_page'] = search_results_page
    return render(request, 'zhihu/search_result.html', context)

def custom_page_not_found(request, exception):
    '''404错误'''
    # 自定错误404错误视图, 需调用系统默认的page_not_found视图
    from django.views.defaults import page_not_found
    res = page_not_found(request, exception, template_name='404.html')
    return res

def server_error(request):
    '''500错误'''
    return render(request, '500.html', status=500)