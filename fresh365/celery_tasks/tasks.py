from celery import Celery
from django.core.mail import send_mail
from django.conf import settings


# 创建一个celery对象 第一个参数是给其设定一个名字， 第二参数我们设定一个中间人broker
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/1')


# 创建任务函数
@app.task
def send_email_2_user(username, token, email):
    html_msg = '<h5>欢迎您＠%s</h5>请点击下面的链接来激活您的账号<br>' \
               '<a href="http://127.0.0.1:8000/user/active/%s">' \
               'http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)
    send_mail('注册激活', '', settings.EMAIL_FROM, [email], html_message=html_msg)
    # 响应请求