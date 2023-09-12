# About

打包、加密、上传、自动清理

使用tar打包，zip加密

使用Minio库上传，路径默认为 \<endpoint\>/\<bucket\>/\<hostname\>\_\<ip\>/autobackup_yymmddHHMMSS.zip

可上传至多个endpoint



# 安装

```
pip install minio pytz cryptography
git clone https://github.com/sseaky/backup_to_oss2.git && cd backup_to_oss2
```

复制config_example.sh为config.sh，并修改配置信息

```
cp config_example.py config.py
vi config.py
```



# 使用

| 参数          | 作用                                  |
| ------------- | ------------------------------------- |
| --backup      | 打包文件并上传                        |
| --list        | 列出oss上当前目录下所有文件，提示下载 |
| --download    | 下载指定文件                          |
| --with-status | 备份时，可保存客户端的一些状态信息    |
| --verbose     | 详细输出                              |
| --tar         | 打包成tar，不加密                     |
| --enc-text    | 使用enc-key加密字串                   |
| --enc-key     | 加密key                               |

```
python3 backup.py --backup --verbose
```

每天备份，使用crontab

```
32 0 * * * cd ~/git/backup_to_oss2 && python3 backup.py --backup --with-status
```



# pyarmor

```
pip install pyarmor
pyarmor g config.py backup.py
```

