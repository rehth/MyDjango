import os
import django
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader
# 配置环境django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fresh365.settings")
django.setup()
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner

# 创建一个celery对象 第一个参数是给其设定一个名字， 第二参数我们设定一个中间人broker
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/1')


# 创建任务函数
@app.task
def send_email_2_user(name, token, to_email):
    email_from = settings.EMAIL_FROM
    send_list = [to_email]
    html_msg = '<h5>欢迎您＠%s</h5>请点击下面的链接来激活您的账号<br>' \
               '<a href="http://127.0.0.1:8000/user/active/%s">' \
               'http://127.0.0.1:8000/user/active/%s</a>' % (name, token, token)
    # 'subject', 'message', 'from_email', and 'recipient_list'
    send_mail(subject='注册激活', message='', from_email=email_from, recipient_list=send_list, html_message=html_msg)


# 生成静态页面的任务函数
@app.task
def generate_static_index_html():
    # 1.商品种类显示
    goods_types = GoodsType.objects.all()
    # 2.首页轮播商品展示
    banner = IndexGoodsBanner.objects.all().order_by('index')
    # 3.首页促销活动
    promotion = IndexPromotionBanner.objects.all().order_by('index')
    # 4.首页分类商品展示(图片/文字)
    for goods_type in goods_types:
        # 查询显示模式为标题的商品
        title = IndexTypeGoodsBanner.objects.filter(goods=goods_type, display_type=0)
        jpg = IndexTypeGoodsBanner.objects.filter(goods=goods_type, display_type=1)
        goods_type.title = title
        goods_type.banner = jpg
    # 5.购物车的中商品的数量 未登录时为0
    cart_content = 0
    # 构建上下文
    context = {'goods_types': goods_types, 'banner': banner,
               'promotion': promotion, 'cart_content': cart_content}

    # 1.加载模板文件, 返回一个模板对象
    temp = loader.get_template('index.html')
    # 2.模板渲染: 产生替换变量后的内容
    static_html = temp.render(context)
    # 3.静态index.html文件生成
    static_save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(static_save_path, 'w') as f:
        f.write(static_html)

