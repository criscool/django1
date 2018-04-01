from django.db import models
from  utils.models import BaseModel
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(BaseModel,AbstractUser):
    class Meta:
        db_table='df_user'


class AreaInfo(models.Model):
    title=models.CharField(max_length=20)
    aParent=models.ForeignKey('self',null=True,blank=True)
    class Meta:
        db_table='df_area'

class Address(BaseModel):
    """地址"""
    user = models.ForeignKey(User, verbose_name="所属用户")
    receiver = models.CharField(max_length=20, verbose_name="收件人")
    phone_number = models.CharField(max_length=11, verbose_name="联系电话")
    addr = models.CharField(max_length=256, verbose_name="详细地址")
    code = models.CharField(max_length=6, verbose_name="邮政编码")
    province=models.ForeignKey(AreaInfo,related_name='province')
    city=models.ForeignKey(AreaInfo,related_name='city')
    district=models.ForeignKey(AreaInfo,related_name='district')
    isDefault=models.BooleanField(default=False)

    class Meta:
        db_table = "df_address"
