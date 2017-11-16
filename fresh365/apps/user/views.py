from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic import View
from apps.user.models import User
from celery_tasks.tasks import send_email_2_user
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired   # 解析异常
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required    # 验证登录的装饰器
import re
# Create your views here.


# /user/register
class Register(View):
    """注册视图"""
    def get(self, request):
        """返回注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """对注册信息进行处理"""
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 数据校验
        if not all([username, password, email]):
            # 检查数据信息是否完整
            return render(request, 'register.html', context={'errmsg': '数据信息不完整'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            # 邮箱格式错误
            return render(request, 'register.html', context={'errmsg': '邮箱格式错误'})
        if password != request.POST.get('cpwd'):
            # 两次密码不相等
            return render(request, 'register.html', context={'errmsg': '两次密码不相等'})
        if allow != 'on':
            return render(request, 'register.html', context={'errmsg': '未同意协议'})
            # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        else:
            return render(request, 'register.html', context={'errmsg': '用户名已存在'})
        # 业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0   # 账号置为未激活状态
        user.save()
        # 发送激活邮件
        # 生成serializer对象，并设置过期时间
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info).decode()  # bytes
        # 调用celery发送邮件
        send_email_2_user.delay(username, token, email)

        # 响应请求
        return redirect(reverse('goods:index'))


# user/active/id
class Active(View):
    """激活视图"""
    def get(self, request, val):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 获取激活用户的id
            user_id = serializer.loads(val)['confirm']
            # 查询用户
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired:
            return HttpResponse('链接失效')


# /user/login
class Login(View):
    """登录视图"""
    def get(self, request):
        username = ''
        checked = ''
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        return render(request, 'login.html', {'username': username, 'checked':checked})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')
        user = authenticate(username=username, password=password)
        # 验证
        if user is not None:
            # 是否激活
            if user.is_active:
                login(request, user)
                response = redirect(reverse('goods:index'))
                # 是否记住用户名
                if remember == 'on':
                    response.set_cookie('username', username)
                else:
                    response.delete_cookie('username')
                return response
        else:
            # 错误
            return render(request, 'login.html')


# /user
class UserCenter(View):
    """用户中心视图"""
    def get(self, request):
        return render(request, 'user_center_info.html')



