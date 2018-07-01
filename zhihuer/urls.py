from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from zhihu.views import index, question_detail, answer_detail, explore, topic_list, topic_detail, add_follow_answer, cancel_follow_answer, comment_answer, follow_question\
    , collect_answer, follow_topic, ask_question, question_list, answer_question, topic_question, topic_answerer, follow_topic_user, explore_recommend
from user.views import register, user_login, user_logout, user_confirm, resend_confirm_email, user_home, user_answer, user_question, reset_password, get_check_code\
    , edit_profile, update_image, change_password, change_email_request, change_email, user_collect_answer, user_follow_topic, user_follow_question, user_follow_user\
    , user_followed_by_user, user_topic_answer, follow_user, delete_answer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),

    path('question/detail/<int:question_id>/', question_detail, name='question_detail'),
    path('answer/detail/<int:answer_id>/', answer_detail, name='answer_detail'),
    path('explore/', explore, name='explore'),
    path('explore/recommend/', explore_recommend, name='explore_recommend'),

    path('topic_list/', topic_list, name='topic_list'),
    path('topic_detail/<int:topic_id>/', topic_detail, name='topic_detail'),
    path('topic_detail/<int:topic_id>/follow_topic/', follow_topic, name='follow_topic'),
    path('topic_detail/<int:topic_id>/question/', topic_question, name='topic_question'),
    path('topic_detail/<int:topic_id>/answerer/', topic_answerer, name='topic_answerer'),
    path('topic_detail/<int:topic_id>/follow_topic_user/', follow_topic_user, name='follow_topic_user'),

    # path('answer/detail/<int:answer_id>/add_follow_answer/', add_follow_answer, name='add_follow_answer'),
    path('answer/add_follow_answer/', add_follow_answer, name='add_follow_answer'),
    # path('answer/detail/<int:answer_id>/cancel_follow_answer/', cancel_follow_answer, name='cancel_follow_answer'),
    path('answer/cancel_follow_answer/', cancel_follow_answer, name='cancel_follow_answer'),
    path('answer/detail/<int:answer_id>/comment_answer/', comment_answer, name='comment_answer'),
    # path('answer/detail/<int:answer_id>/collect_answer/', collect_answer, name='collect_answer'),
    path('answer/collect_answer/', collect_answer, name='collect_answer'),
    # path('question/detail/<int:question_id>/follow_question/', follow_question, name='follow_question'),
    path('question/follow_question/', follow_question, name='follow_question'),
    
    path('ask_question/', ask_question, name='ask_question'),
    path('question_list/', question_list, name='question_list'),
    path('question/detail/<int:question_id>/answer_question/', answer_question, name='answer_question'),

    # 用户
    path('register/', register, name='register'),
    path('login/', user_login, name='user_login'),
    path('logout/', user_logout, name='user_logout'),
    path('confirm/<str:token>/', user_confirm, name='user_confirm'),
    path('resend_confirm_email/', resend_confirm_email, name='resend_confirm_email'),
    path('user/<int:user_id>/home/', user_home, name='user_home'),
    path('user/<int:user_id>/answer/', user_answer, name='user_answer'),
    path('user/<int:user_id>/question/', user_question, name='user_question'),
    path('reset_password/', reset_password, name='reset_password'),
    path('reset_password/get_check_code/', get_check_code, name='get_check_code'),
    path('user/edit_profile/', edit_profile, name = 'edit_profile'),
    path('user/edit_profile/update_image/', update_image, name = 'update_image'),
    path('user/edit_profile/change_password/', change_password, name='change_password'),
    path('user/edit_profile/change_email_request/', change_email_request, name='change_email_request'),
    path('user/edit_profile/change_email/<str:token>/', change_email, name='change_email'),
    path('user/<int:user_id>/collect_answer/', user_collect_answer, name='user_collect_answer'),
    path('user/<int:user_id>/follow_topic/', user_follow_topic, name='user_follow_topic'),
    path('user/<int:user_id>/follow_question/', user_follow_question, name='user_follow_question'),
    path('user/<int:user_id>/follow_user/', user_follow_user, name='user_follow_user'),
    path('user/<int:user_id>/followed_by_user/', user_followed_by_user, name='user_followed_by_user'),
    path('user/<int:user_id>/topic_answer/<int:topic_id>/', user_topic_answer, name='user_topic_answer'),
    path('user/follow/', follow_user, name='follow_user'),
    path('user/delete_answer/', delete_answer, name='delete_answer'),
]

# 第三方验证码url配置
urlpatterns += [path('captcha/', include('captcha.urls'))]
# 在调试模式中访问用户上传文件需配置
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# 富文本编辑器
urlpatterns += [re_path('^ckeditor/', include('ckeditor_uploader.urls'))]