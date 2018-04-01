from django.shortcuts import render
from .models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner
from django.core.cache import cache
from .models import GoodsSKU
from django.http import Http404
from django_redis import get_redis_connection


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