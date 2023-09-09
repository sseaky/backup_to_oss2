# About

打包、加密、上传、自动清理

使用tar打包，zip加密

使用Minio库上传，路径默认为 \<endpoint\>/\<bucket\>/\<hostname\>\_\<ip\>/autobackup_yymmddHHMMSS.zip

可上传至多个endpoint



# 安装

```
git clone https://github.com/sseaky/backup_to_oss.git2
```

复制config_example.sh为config.sh，并修改配置信息

```
cd backup_to_oss2
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



```
python3 backup.py --backup --verbose
```

每天备份，使用crontab

```
0 0 * * * cd <path>/backup_to_oss && python3 backup.py --backup --with-status
```

