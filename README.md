# django开发简单的仿知乎网站

- 使用 python3.5.2 + django2.0.3 开发
- 前端使用 bootstrap3
- 在本地虚拟机 ubuntu 中使用 nginx + uwsgi 部署成功



项目部署在 pythonanywhere 网站.   点击访问 [zhihuer](https://taoing.pythonanywhere.com/)

懒得注册的话, 这里有一个账户可供观光:

- 账户: tester
- 密码: test123456

------

由于pythonanywhere的免费账户无法访问国内的邮箱, 无法使用国内发送邮件, 文档说使用gmail, 我使用gmail一致都是认证失败, 更改了设置也还是没有用. 所以网站是无法发送邮件的.

------



### 简单的仿知乎网站

实现功能: 

1. 提问和回答, 点赞回答, 收藏回答和提问, 评论回答
2. 用户注册登录, 用户个人主页, 用户相互关注
3. 话题功能, 话题关注
4. 发现页面, 推荐
5. 简单的搜索功能
