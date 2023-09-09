# 基础调协
CLIENT_NAME = ''  # BUCKET中的目录名，如果为空，则自动命名为<hostname>_<default_ip>

# 打包设置，修改ZIP密码
METHOD = 'zip'
ZIP_PASSWORD = '123456'
BACKUP_FILE_STEM = 'autobackup'
DAYS_TO_RETAIN = 30
MIN_COUNT_TO_KEEP = 5

# 要备份的文件或目录
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
