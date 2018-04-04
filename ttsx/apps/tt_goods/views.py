from django.shortcuts import render
from .models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner
from django.core.cache import cache
from .models import GoodsSKU
from django.http import Http404
from django_redis import get_redis_connection
from django.core.paginator import Paginator,Page
from haystack.generic_views import SearchView
from utils.page_list import get_page_list


# Create your views here.
def fdfs_test(request):
    category = GoodsCategory.objects.get(pk=1)
    context = {'category': category}
    print(type(category.image))
    # django.db.models.fields.files.ImageFieldFile
    return render(request, 'fdfs_test.html', context)


def index(request):
    #先向缓存中读取
    context = cache.get('index')
    if context==None:

        # 查询分类信息
        category_list = GoodsCategory.objects.all()

        # 查询轮播图片
        banner_list = IndexGoodsBanner.objects.all().order_by('index')

        # 查询广告
        adv_list = IndexPromotionBanner.objects.all().order_by('index')

        # 查询每个分类的推荐产品
        for category in category_list:
            # 查询推荐的标题商品，当前分类的，按照index排序的，取前3个
            category.title_list = IndexCategoryGoodsBanner.objects.filter(display_type=0, category=category).order_by(
                'index')[0:3]
            # 查询推荐的图片商品
            category.img_list = IndexCategoryGoodsBanner.objects.filter(display_type=1, category=category).order_by(
                'index')[0:4]

        context = {
            'title': '首页',
            'category_list': category_list,
            'banner_list': banner_list,
            'adv_list': adv_list,
        }
        #设置缓存
        cache.set('index',context,3600)



    response= render(request, 'index.html', context)
    return response


def detail(request, sku_id):
    # 查询商品信息
    try:
        sku = GoodsSKU.objects.get(pk=sku_id)
    except:
        raise Http404()

    # 查询分类信息
    category_list = GoodsCategory.objects.all()

    # 查询新品推荐：当前商品所在分类的最新的两个商品
    # new_list=GoodsSKU.objects.filter(category=sku.category).order_by('-id')[0:2]
    # 根据多找一：sku.category商品对应的分类对象
    category = sku.category
    # 根据一找多：分类对象.模型类小写_set
    new_list = category.goodssku_set.all().order_by('-id')[0:2]

    # 查询当前商品对应的所有陈列
    # 根据当前sku找到对应的spu，已经“盒装草莓”，找“草莓”
    goods = sku.goods
    # 根据spu找所有的sku，已经“草莓”，找所有的“草莓sku”，如“盒装草莓”、“论斤草莓”...
    other_list = goods.goodssku_set.all()
    # 最近浏览
    if request.user.is_authenticated():
        redis_client = get_redis_connection()
        # 构造键
        key = 'history%d' % request.user.id
        # 如果当前编号已经存在，则删除
        redis_client.lrem(key, 0, sku_id)  # 删除所有的指定元素
        # 将当前编号加入
        redis_client.lpush(key, sku_id)  # 向列表的左侧添加一个元素
        # 不能超过5个，则删除
        if redis_client.llen(key) > 5:  # 判断列表的元素个数
            redis_client.rpop(key)  # 从列表的右侧删除一个元素

    context = {
        'title': '商品详情',
        'sku': sku,
        'category_list': category_list,
        'new_list': new_list,
        'other_list': other_list,
    }

    return render(request, 'detail.html', context)


def list_sku(request,category_id):
    #查询当前分类对象
    try:
        category_now=GoodsCategory.objects.get(pk=category_id)
    except:
        raise Http404()

    # 接收排序规则
    order = int(request.GET.get('order', 1))
    if order == 2:
        order_by = '-price'  # 按照价格降序
    elif order == 3:
        order_by = 'price'  # 按照价格升序
    elif order == 4:
        order_by = '-sales'  # 按照销量降序
    else:
        order_by = '-id'  # 按照编号降序排列

    #查询当前分类的所有商品
    sku_list=GoodsSKU.objects.filter(category_id=category_id).order_by(order_by)

    #查询所有分类信息
    category_list=GoodsCategory.objects.all()

    #当前分类的最新的两个商品
    new_list=category_now.goodssku_set.all().order_by('-id')[0:2]

    #分页
    paginator=Paginator(sku_list,1)
    # 总页数
    total_page = paginator.num_pages
    # 接收页码值，进行判断
    pindex = int(request.GET.get('pindex', 1))
    if pindex < 1:
        pindex = 1
    if pindex > total_page:
        pindex = total_page
    # 查询指定页码的数据
    page=paginator.page(pindex)

    # 构造页码的列表，用于提示页码链接
    page_list = []  # 3 4 5 6 7==>range(n-2,n+3)
    if total_page <= 5:  # 如果不足5页，则显示所有数字
        page_list = range(1, total_page + 1)
    elif pindex <= 2:  # 如果是前两页，则显示1-5
        page_list = range(1, 6)
    elif pindex >= total_page - 1:  # 如果是最后两页，则显示最后5页
        page_list = range(total_page - 4, total_page + 1)  # 共18页，则最后的数字是14 15 16 17 18
    else:
        page_list = range(pindex - 2, pindex + 3)
    # page_list = get_page_list(total_page, pindex)
    context={
        'title':'商品列表',
        'page':page,
        'category_list':category_list,
        'category_now':category_now,
        'new_list':new_list,
        'order':order,
        'page_list':page_list,

    }
    return render(request,'list.html',context)


class MySearchView(SearchView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title']='搜索结果'
        context['category_list']=GoodsCategory.objects.all()

        #页码控制
        total_page=context['paginator'].num_pages
        pindex=context['page_obj'].number
        context['page_list']=get_page_list(total_page,pindex)

        return context