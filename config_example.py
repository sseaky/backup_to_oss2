# 打包设置
ZIP_PASSWORD = '12345678'
BACKUP_FILE_STEM = 'autobackup'
DAYS_TO_RETAIN = 60
MIN_COUNT_TO_KEEP = 5

# 基础配置
CLIENT_NAME = ''  # BUCKET中的目录名，如果为空，则自动为<hostname>_<ip>

# 状态文件
STATUS_FILE_PATH = '/tmp/myState.txt'
STATUS_COMMANDS = [
    'hostname',
    'uptime',
    'w',
    'last',
    'lastb',
    'free -h',
    'mount',
    'df -h',
    'ip a',
    'ip route',
    'ip -6 route',
    'iptables-save',
    'netstat -anop',
    'netstat -lntup',
    'docker ps -a',
    'docker images',
]

# 要备份的文件或目录，以空格或换行分割
SOURCE_PATH = [
    '/etc/os-release',
    '/etc/motd',
    '/etc/hosts',
    '/etc/passwd',
    '/etc/nginx',
    '/etc/zabbix',
    '/backup',
]

# exclude匹配目录时，*不要*在最后加 /
# tar cvf a1.tar --exclude='*.log' --exclude='*.tmp' --exclude='*/.env' --exclude='*/.git' -C /root/test/ .
SOURCE_EXCLUDE = [
    '*.log',
    '*.tmp',
    '*/.env',
    '*/.git'
]

HTTP_PROXY = None

# 可配置多个OSS服务器。backup时会上传至所有可用的服务器，list/download时使用第1个可用的服务器
OSS_CONFIGS = [
    {
        'url': 'https://',
        'access_key': '',
        'secret_key': '',
        'bucket_name': '',
    }
]

# DECRYPTO，将会使用DECRYPTO_KEY对url、access_key、secret_key解密
DECRYPTO = True
DECRYPTO_KEY = ''
