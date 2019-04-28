from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth import get_user_model
from django.db import models

from user.models import User


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]


class Topic(models.Model):
    '''话题分类'''
    name = models.CharField('话题', max_length=40)
    description = models.CharField('话题描述', max_length=200, null=True,
                                   blank=True)
    add_time = models.DateTimeField('添加时间', auto_now_add=True)
    image = models.ImageField('话题图片', upload_to='image/%Y/%m/',
                              default='image/default_topic.jpg', null=True,
                              blank=True)

    users = models.ManyToManyField(User, blank=True, verbose_name='用户话题')

    def __str__(self):
        return self.name

    def get_user_nums(self):
        '''获取关注者数量'''
        return self.users.count()

    def get_question_nums(self):
        '''获取话题的问题数'''
        return self.question_set.count()


class Question(models.Model):
    '''问题模型'''
    title = models.CharField('问题标题', max_length=200)
    author = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user),
                               verbose_name='问题作者')
    content = models.TextField('问题内容', null=True, blank=True)
    topics = models.ManyToManyField(Topic, blank=True, verbose_name='话题')
    pub_time = models.DateTimeField('发布时间', auto_now_add=True)
    recommend = models.BooleanField('是否推荐', default=False)
    read_nums = models.IntegerField('浏览量', default=0)
    is_anonymous = models.BooleanField('匿名问题', default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-pub_time']

    def get_answer_nums(self):
        '''获取回答数量'''
        return self.answer_set.count()

    def get_follow_est_answer(self):
        '''获取点赞最多的回答'''
        return self.answer_set.annotate(
            follow_nums=models.Count('userfollowanswer')).order_by(
            '-follow_nums').first()

    def get_topic_name(self):
        '''获取话题名'''
        return self.topics.first().name

    def get_follow_nums(self):
        '''获取关注者数量'''
        return self.userfollowquestion_set.count()


def get_sentinel_question():
    return Question.objects.get_or_create(title='deleted question')[0]


class Answer(models.Model):
    '''回答模型'''
    question = models.ForeignKey(Question,
                                 on_delete=models.SET(get_sentinel_question),
                                 verbose_name='回答问题')
    author = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user),
                               verbose_name='回答作者')
    content = RichTextUploadingField('回答内容')
    pub_time = models.DateTimeField('发布时间', auto_now_add=True)
    voteup_nums = models.IntegerField('认同数', default=0)
    votedown_nums = models.IntegerField('不认同数', default=0)
    is_anonymous = models.BooleanField('匿名回答', default=False)

    def get_follow_nums(self):
        '''获取回答点赞数'''
        return self.userfollowanswer_set.count()

    def get_collect_nums(self):
        '''获取回答的被收藏数'''
        return self.usercollectanswer_set.count()

    def get_comment_nums(self):
        '''获取评论数量'''
        return self.answercomment_set.count()

    def __str__(self):
        return self.content[:50]


class AnswerComment(models.Model):
    '''回答评论模型'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE,
                               verbose_name='回答')
    comment = models.CharField('评论', max_length=300)
    add_time = models.DateTimeField('添加时间', auto_now_add=True)

    def __str__(self):
        return self.comment[:50]


class UserFollowQuestion(models.Model):
    '''用户关注问题模型'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    question = models.ForeignKey(Question, on_delete=models.CASCADE,
                                 verbose_name='问题')
    add_time = models.DateTimeField('添加时间', auto_now_add=True)


class UserFollowAnswer(models.Model):
    '''用户点赞回答模型'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE,
                               verbose_name='回答')
    add_time = models.DateTimeField('添加时间', auto_now_add=True)


class UserCollectAnswer(models.Model):
    '''用户收藏回答模型'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE,
                               verbose_name='回答')
    add_time = models.DateTimeField('添加时间', auto_now_add=True)
