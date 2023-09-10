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
    'mount',
    'df -h',
    'ip a',
    'ip route',
    'iptables-save',
    'netstat -anop',
    'netstat -lntup',
    'docker ps -a',
]

# 打包设置
METHOD = 'zip'
ZIP_PASSWORD = 'w2kv4nTY5fH6'
BACKUP_FILE_STEM = 'autobackup'
DAYS_TO_RETAIN = 60
MIN_COUNT_TO_KEEP = 5

# 要备份的文件或目录，以空格或换行分割
SOURCE_PATH = [
    '/etc/hosts',
    '/etc/passwd',
    '/etc/nginx'
]

# exclude匹配目录时，*不要*在最后加 /
# tar cvf a1.tar --exclude='*.log' --exclude='*.tmp' --exclude='*/.env' --exclude='*/.git' -C /root/test/ .
SOURCE_EXCLUDE = [
    '*.log',
    '*.tmp',
    '*/.env',
    '*/.git'
]

# 可配置多个OSS服务器。backup时会上传至所有可用的服务器，list/download时使用第1个可用的服务器
OSS_CONFIGS = [
    {
        'url': 'https://',
        'access_key': '',
        'secret_key': '',
        'bucket_name': '',
    }
]

HTTP_PROXY = None

# 如果设置了str，将会对ZIP_PASSWORD、access_key、secret_key解密
DECRYPTO_KEY = None
