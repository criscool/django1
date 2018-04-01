# -*- coding:utf-8 -*-

#python连接FastDFS服务器的驱动
from fdfs_client.client import Fdfs_client
#根据配置文件创建连接的客户端
client=Fdfs_client()
#调用方法上传文件
result=client.upload_by_file('01.jpg')
#上传成功返回结果
print(result)
