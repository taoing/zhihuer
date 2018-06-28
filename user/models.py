from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core import signing

class User(AbstractUser):
    '''用户模型'''
    gender_choices = (
        ('M', '男'),
        ('F', '女')
        )
    nickname = models.CharField('昵称', max_length=40, null=True, blank=True)
    email = models.EmailField('邮箱')
    gender = models.CharField('性别', choices=gender_choices, max_length=1, default='M')
    address = models.CharField('居住地', max_length=100, null=True, blank=True)
    description = models.CharField('个人描述', max_length=400, null=True, blank=True)
    image = models.ImageField('用户头像', upload_to='image/%Y/%m', default='image/default_user.png', null=True, blank=True)
    confirmed = models.BooleanField('用户确认', default=False)
    # add_time = models.DateTimeField('加入时间', auto_now_add=True)

    #用户相互关注, 多对多关系字段
    users = models.ManyToManyField('self', through='UserRelationship', symmetrical=False, verbose_name='关注')

    def __str__(self):
        return self.username

    def get_topic_nums(self):
        return self.topic_set.all().count()

    def get_collect_answer_nums(self):
        return self.usercollectanswer_set.all().count()

    def get_follow_question_nums(self):
        return self.userfollowquestion_set.all().count()

    def get_answer_by_followed_nums(self):
        '''获取所有回答的被关注数量'''
        from zhihu.models import UserFollowAnswer
        return UserFollowAnswer.objects.filter(answer__author=self).count()

    def get_answer_by_collected_nums(self):
        '''获取所有回答的被关注数量'''
        from zhihu.models import UserCollectAnswer
        return UserCollectAnswer.objects.filter(answer__author=self).count()

    def generate_confirm_token(self):
        '''生成用户确认签名'''
        token = signing.dumps({'confirm': self.id})
        return token

    def confirm(self, token, max_age=24*60*60):
        '''验证确认签名'''
        try:
            data = signing.loads(token, max_age=max_age)
        except Exception as e:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        self.save()
        return True

    def generate_change_email_token(self, new_email):
        '''生成修改邮箱签名'''
        token = signing.dumps({'change_email':self.id, 'new_email':new_email})
        return token

    def confirm_change_email(self, token, max_age=10*60):
        '''确认签名, 修改邮箱'''
        try:
            data = signing.loads(token, max_age=max_age)
        except Exception as e:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if User.objects.filter(email=new_email):
            return False
        self.email = new_email
        self.save()
        return True

    def get_follow_user_nums(self):
        '''获取用户关注的用户数量'''
        return self.to_user_set.count()

    def get_followed_by_user_nums(self):
        '''获取关注该用户的用户数量'''
        return self.from_user_set.count()


class CheckCode(models.Model):
    '''用户验证码模型'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    check_code = models.CharField('验证码', max_length=8)
    # 每次保存时自动更新创建时间
    add_time = models.DateTimeField('创建时间', auto_now=True)

    def __str__(self):
        return self.check_code


class UserRelationship(models.Model):
    '''用户相关关注中间模型, 显式定义'''
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='to_user_set',verbose_name='用户')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='from_user_set', verbose_name='关注')
    add_time = models.DateTimeField('关注时间', auto_now_add=True)