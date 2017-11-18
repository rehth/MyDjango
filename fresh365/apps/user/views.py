from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic import View
from apps.user.models import User, Address
from apps.goods.models import GoodsSKU
from celery_tasks.tasks import send_email_2_user
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired   # 解析异常
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required    # 验证登录的装饰器
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection   # 创建与redis连接的类
import re
# Create your views here.


# def test_fdsf(request):
#     """测试FastDFS"""
#     return render(request, 'test.html')

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
            User.objects.get(username=username)
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
        # 获取next的值, 如果没有则返回　reverse('goods:index')
        next_url = request.GET.get('next', reverse('goods:index'))
        # 验证
        if user is not None:
            # 是否激活
            if user.is_active:
                login(request, user)
                response = redirect(next_url)
                # 是否记住用户名
                if remember == 'on':
                    response.set_cookie('username', username)
                else:
                    response.delete_cookie('username')
                return response
        else:
            # 错误
            return render(request, 'login.html')


# /user/logout
class Logout(View):
    """退出视图"""
    def get(self, request):
        """清除sessions"""
        logout(request)
        return redirect(reverse('goods:index'))


# /user
class UserCenter(LoginRequiredMixin):
    """用户中心-信息视图"""
    def get(self, request):
        context = {'page': 'center'}
        # 用户的基本信息
        user = request.user
        address = Address.objects.get_default_address(user)
        context['user'] = user
        context['address'] = address
        # 用户的浏览记录
        # 1.获取redis连接对象
        con = get_redis_connection("default")
        # 2.用户id
        list_id = 'history_%s' % user.id
        # 3.取出5个最近浏览的商品id
        goods_sku_list = con.lrange(list_id, 0, 4)
        # 4.商品列表
        goods_list = list()
        # 5.循环从GoodsSKU表中根据id查询商品信息 添加到列表中
        for goods_id in goods_sku_list:
            goods_list.append(GoodsSKU.objects.get(id=goods_id))
        # 6.添加到上下文中
        context['goods_list'] = goods_list
        return render(request, 'user_center_info.html', context)


# /user/site
class UserSite(LoginRequiredMixin):
    """用户中心-地址视图"""
    def get(self, request):
        context = {'page': 'site'}
        # 获取用户的收货地址信息(默认)
        # 1.获取所属用户
        user = request.user
        # 2.查询用户是否存在默认地址 若没有则返回None
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None

        address = Address.objects.get_default_address(user)
        context['address'] = address
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        """地址添加"""
        # 接受数据
        receiver = request.POST.get('receiver')
        site = request.POST.get('site')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 数据校验
        if not all([receiver, site, phone]):
            return redirect(reverse('user:site'))
        if not re.match(r'^1[34578][0-9]{9}$', phone):
            return redirect(reverse('user:site'))
        # 业务处理 地址添加
        # 1.获取所属用户
        user = request.user
        # 2.检查用户是否存在默认地址 若没有则创建默认地址(is_default=True)
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None

        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True
        # 3.创建用户
        Address.objects.create(user=user, receiver=receiver, addr=site,
                               zip_code=zip_code, phone=phone, is_default=is_default)
        # 返回应答
        return redirect(reverse('user:site'))


# /user/order
class UserOrder(LoginRequiredMixin):
    """用户中心-订单视图"""
    def get(self, request):
        context = {'page': 'order'}
        # 获取用户的订单详细信息

        return render(request, 'user_center_order.html', context)
