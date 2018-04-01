from django.shortcuts import render,redirect
from django.views.generic import View
from .models import User,Address,AreaInfo
import re
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired
# from celery_tasks.tasks import send_user_active
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from utils.views import LoginRequiredView, LoginRequiredViewMixin
from django_redis import get_redis_connection
from tt_goods.models import GoodsSKU



# Create your views here.
# def register(request):
#     return render(request,'register.html')
class RegisterView(View):
    def get(self,request):
        return render(request,'register.html')
    def post(self,request):
        #接收数据
        dict = request.POST
        uname = dict.get('user_name')
        pwd = dict.get('pwd')
        cpwd = dict.get('cpwd')
        email = dict.get('email')
        uallow = dict.get('allow')
        #结果数据
        context = {
            'uname': uname,
            'pwd': pwd,
            'email': email,
            'cpwd': cpwd,
            'err_msg': '',
            'title':'注册处理',
        }
        #　判读数据的有效性

        # 1.判断是否接收协议
        if uallow is None:
            context['err_msg'] = '请接收协议'
            return render(request, 'register.html', context)
        # 2.验证数据不为空
        if not all([uname, pwd, cpwd, email]):
            context['err_msg'] = '请填写完整信息'
            return render(request, 'register.html', context)
        # 3.判读两个密码是否一致
        if pwd != cpwd:
            context['err_msg'] = '两次密码不一致'
            return render(request, 'register.html', context)
        # 4.用户名不能重复
        if User.objects.filter(username=uname).count() > 0:
            context['err_msg'] = '用户名已经存在'
            return render(request, 'register.html', context)
        # 5.邮箱格式是否正确
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            context['err_msg'] = '邮箱格式不正确'
            return render(request, 'register.html', context)
        # 6.邮箱是否存在
        # if User.objects.filter(email=email).count()>0:
        #     context['err_msg']='邮箱已经被注册'
        #     return render(request,'register.html',context)
        # 保存对象
        user = User.objects.create_user(uname, email, pwd)
        user.is_active = False
        user.save()

        # #加密用户编号
        serializer=Serializer(settings.SECRET_KEY,60*60)
        value=serializer.dumps({'id':user.id}).decode()
        #
        # # #让用户激活：向注册的邮箱发邮件，点击邮件中的链接，转到本网站的激活地址r
        msg='<a href="http://127.0.0.1:8000/user/active/%s">点击激活</a>'%value
        send_mail('天天生鲜-账户激活','',settings.EMAIL_FROM,[email],html_message=msg)

        # 提示
        return HttpResponse('注册成功，请稍候到邮箱中激活账户')

def active(request,value):
    # 解密
    try:
        serializer = Serializer(settings.SECRET_KEY)
        dict = serializer.loads(value)
    except SignatureExpired as e:
        return HttpResponse('链接已经过期')

    # 激活指定的账户
    uid = dict.get('id')
    user = User.objects.get(pk=uid)
    user.is_active = True
    user.save()

    return redirect('/user/login')

def exists(request):
    # 接收用户名
    uname = request.GET.get('uname')

    if uname is not None:
        # 判断用户名是否存在
        result = User.objects.filter(username=uname).count()

    # 返回结果
    return JsonResponse({'result': result})

class LoginView(View):
    def get(self, request):
        uname=request.COOKIES.get('uname','')
        context={
            'title': '登录',
            'uname':uname
        }
        return render(request, 'login.html',context)

    def post(self, request):
        # 接收数据
        dict = request.POST
        uname = dict.get('username')
        upwd = dict.get('pwd')
        remember=dict.get('remember')

        # 构造返回结果
        context = {
            'uname': uname,
            'upwd': upwd,
            'err_msg': '',
            'title':'登录处理',
        }

        # 判断数据是否填写
        if not all([uname, upwd]):
            context['err_msg'] = '请填写完整信息'
            return render(request, 'login.html', context)

        # 判断用户名、密码是否正确
        user = authenticate(username=uname, password=upwd)

        if user is None:
            context['err_msg'] = '用户名或密码错误'
            return render(request, 'login.html', context)

        # 如果未激活也不允许登录
        if not user.is_active:
            context['err_msg'] = '请先到邮箱中激活'
            return render(request, 'login.html', context)

        # 状态保持
        login(request, user)

        # 获取next参数，转回到之前的页面
        # http://127.0.0.1:8000/user/login?next=/user/order
        # http://127.0.0.1:8000/user/login?next=/user/site
        next_url = request.GET.get('next', '/user/info')
        response = redirect(next_url)

        #记住用户名
        if remember is None:
            response.delete_cookie('uname')
        else:
            response.set_cookie('uname',uname,expires=60*60*24*7)

        # 如果登录成功则转到用户中心页面
        return response

def logout_user(request):
    #退出用户
    logout(request)

    return redirect('/user/login')

@login_required
def info(request):
    # 如果用户未登录，则转到登录页面
    # if not request.user.is_authenticated():
    #     return redirect('/user/login?next='+request.path)

    # 查询当前用户的默认收货地址,如果没有数据则返回[]
    address = request.user.address_set.filter(isDefault=True)
    if address:
        address = address[0]
    else:
        address = None

    # 获取redis服务器的连接,根据settings.py中的caches的default获取
    redis_client = get_redis_connection()
    # 因为redis中会存储所有用户的浏览记录，所以在键上需要区分用户
    gid_list = redis_client.lrange('history%d' % request.user.id, 0, -1)
    # 根据商品编号查询商品对象
    goods_list = []
    for gid in gid_list:
        goods_list.append(GoodsSKU.objects.get(pk=gid))

    context = {
        'title': '个人信息',
        'address': address,
        'goods_list': goods_list
    }
    return render(request, 'user_center_info.html', context)

@login_required
def order(request):
    context = {}
    return render(request, 'user_center_order.html', context)

# django中类视图添加装饰器推荐的方案Mixin
# class SiteView(View):RedirectView
# class SiteView(LoginRequiredView):
class SiteView(LoginRequiredViewMixin, View):  # RedirectView
    def get(self, request):
        # 查询当前用户的收货地址
        addr_list = Address.objects.filter(user=request.user)

        context = {
            'title': '收货地址',
            'addr_list': addr_list,
        }
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        # 接收数据
        dict = request.POST
        receiver = dict.get('receiver')
        provice = dict.get('provice')  # 选中的option的value值
        city = dict.get('city')
        district = dict.get('district')
        addr = dict.get('addr')
        code = dict.get('code')
        phone = dict.get('phone')
        default = dict.get('default')

        # 验证有效性
        if not all([receiver, provice, city, district, addr, code, phone]):
            return render(request, 'user_center_site.html', {'err_msg': '信息填写不完整'})

        # 保存数据
        address = Address()
        address.receiver = receiver
        address.province_id = provice
        address.city_id = city
        address.district_id = district
        address.addr = addr
        address.code = code
        address.phone_number = phone
        if default:
            address.isDefault = True
        address.user = request.user
        address.save()

        # 返回结果
        return redirect('/user/site')


def area(request):
    # 获取上级地区的编号
    pid = request.GET.get('pid')

    if pid is None:
        # 查询省信息[area,]
        slist = AreaInfo.objects.filter(aParent__isnull=True)
    else:
        # 查询指定pid的子级地区
        # 如果pid是省的编号，则查出来市的信息
        # 如果pid是市的编号，则查出来区县的信息
        slist = AreaInfo.objects.filter(aParent_id=pid)

    # 将数据的结构整理为：[{id:**,title:***},{},...]
    slist2 = []
    for s in slist:
        slist2.append({'id': s.id, 'title': s.title})

    return JsonResponse({'list': slist2})

