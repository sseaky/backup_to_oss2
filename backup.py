#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ChatGPT, Seaky

import argparse
import os
import re
import subprocess
import pytz
import socket
import getpass
from minio import Minio
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

from config import OSS_CONFIGS, CLIENT_NAME, DAYS_TO_RETAIN, STATUS_FILE_PATH, \
    MIN_COUNT_TO_KEEP, ZIP_PASSWORD, SOURCE_PATH, SOURCE_EXCLUDE, STATUS_COMMANDS, DECRYPTO, DECRYPTO_KEY


def encrypto(string, key):
    key = Fernet.generate_key() if not key else key.encode()
    cipher_suite = Fernet(key)
    encrypted_text = cipher_suite.encrypt(string.strip().encode())
    print(f'text: {string}, key: {key.decode()}, encrypted_text: {encrypted_text.decode()}')


def decrypto(string, key):
    cipher_suite = Fernet(key.encode())
    decrypted_text = cipher_suite.decrypt(string.encode()).decode()
    return decrypted_text


def get_client_name():
    hostname = socket.gethostname()
    default_interface = subprocess.getoutput("ip route | grep default | awk '{print $5}' | head -1")
    ip_address = subprocess.getoutput(
        f'ip addr show {default_interface} | grep \'inet \' | awk \'{{print $2}}\' | cut -d/ -f1')
    if not re.search('^[\d.]+$', ip_address):
        raise 'get default ip address fail!'
    return f'{hostname}_{ip_address}'


def strip_last_slash(string):
    return re.sub('/+$', '', string)


client_name = CLIENT_NAME or get_client_name()


class _Class:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def _print_verbose(self, message):
        if self.verbose:
            print(message)


class OssManger(_Class):
    def __init__(self, url, access_key, secret_key, bucket_name, verbose=False):
        super(OssManger, self).__init__(verbose=verbose)
        self.url = url
        self.bucket_name = bucket_name
        secure = True if url.startswith('https') else False
        endpoint = re.sub('http[s]://', '', url, re.I)
        self.domain = re.sub(':\d+', '', '.'.join(endpoint.split('.')[-2:]))
        self.is_connected = False
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self.check_connection()

    def check_connection(self):
        try:
            # 列出所有的存储桶
            buckets = self.client.list_buckets()
            print(f'\nConnection [{self.domain}] successful!\n')
            self.is_connected = True
        except Exception as e:
            print(f'\nConnection [{self.domain}] fail: {e}\n')

    def create_bucket(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            self._print_verbose(f'Bucket {self.bucket_name} created successfully')

    def upload_object(self, remote_dir, local_file_path):
        remote_dir = strip_last_slash(remote_dir)
        self.create_bucket()
        object_name = f'{remote_dir}/{local_file_path}'
        """Upload the specified file to the specified bucket."""
        self._print_verbose(f'Uploading {local_file_path} to [{self.domain}] {self.bucket_name}/{object_name}')
        result = self.client.fput_object(self.bucket_name, object_name, local_file_path)
        print(f'Uploaded as [{self.domain}] {result.bucket_name}/{result.object_name} with ETag: {result.etag}')

    def prompt_for_download(self, remote_dir):
        remote_dir = strip_last_slash(remote_dir)
        objs = list(self.client.list_objects(self.bucket_name, f'{remote_dir}/'))
        # Number the objects
        print(f'Objects in [{self.domain}] {self.bucket_name}:')
        for i, obj in enumerate(objs, 1):
            print(f"{i}) {obj.object_name} {obj.size}")

        # Prompt the user for a number or 'q' to quit
        while True:
            choice = input("Enter the number of the object you'd like to download, or 'q' to quit: ")

            if choice.lower() == 'q':
                print("Exiting.")
                break

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(objs):
                    self.download_object(objs[choice_num - 1].object_name)
                    break
                else:
                    print(f"Please enter a number between 1 and {len(objs)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit.")

    def download_object(self, object_name):
        file_path = object_name.split('/')[-1]
        self.client.fget_object(self.bucket_name, object_name, file_path)
        print(f'Downloaded {object_name} from bucket {self.bucket_name} to {file_path}')

    def list_objects(self, remote_dir='/'):
        remote_dir = strip_last_slash(remote_dir)
        objects = sorted(
            self.client.list_objects(self.bucket_name, prefix=f'{remote_dir}/'),
            key=lambda x: x.last_modified)
        return objects

    def delete_old_objects(self, remote_dir, days_to_retain, min_count_to_keep):
        current_time_with_tz = datetime.now(pytz.timezone('Asia/Shanghai'))
        objs_to_delete = []
        objects = self.list_objects(remote_dir=remote_dir)

        for obj in objects:
            if len(objects) - len(objs_to_delete) <= min_count_to_keep:
                break
            if current_time_with_tz - obj.last_modified > timedelta(days=days_to_retain):
                objs_to_delete.append(obj.object_name)

        for obj_name in objs_to_delete:
            self.client.remove_object(self.bucket_name, obj_name)
            print(f'Deleted [{self.domain}] {obj_name}')


class Package(_Class):
    def __init__(self, verbose=False):
        super(Package, self).__init__(verbose=verbose)
        self.verbose = verbose

    def _print_verbose(self, message):
        if self.verbose:
            print(message)

    def _safe_subprocess_run(self, command):
        self._print_verbose(f'RUN: {" ".join(command)}')
        output = subprocess.getoutput(' '.join(command))
        return output

    def pack_backup(self, source_path, source_exclude, tar=False, zip_password=None, dereference=False):
        source_list = [x.strip() for x in source_path]
        source_exclude_liset = [x.strip() for x in source_exclude]

        # Define tar and zip names
        current_datetime = datetime.now().strftime('%y%m%d%H%M%S')
        stem = f'autobackup_{current_datetime}'
        tar_name = f'{stem}.tar.gz'
        # Create tar
        tar_command = ['tar', 'zcf']
        tar_command.append(tar_name)
        if dereference:
            tar_command.append('--dereference')
        tar_command += ['--exclude=' + pattern for pattern in source_exclude_liset] + source_list
        self._safe_subprocess_run(tar_command)
        if tar or not zip_password:
            return tar_name

        # Zip with password
        zip_name = f'{stem}.zip'
        zip_command = ['zip', '-P', zip_password, zip_name, tar_name]
        self._safe_subprocess_run(zip_command)
        self.remove(tar_name)
        return zip_name

    def save_status(self, commands, status_file_path):
        with open(status_file_path, 'w') as status_file:
            for cmd in commands:
                output = self._safe_subprocess_run(cmd.split())
                status_file.write(f'# {cmd}\n{output}\n\n')
            crontabs_dir = '/var/spool/cron/crontabs'
            for cron_file in os.listdir(crontabs_dir):
                cron_file_path = os.path.join(crontabs_dir, cron_file)
                if os.path.isfile(cron_file_path):  # Ensure it's a file
                    status_file.write(f'## {cron_file}\n')
                    with open(cron_file_path, 'r') as f:
                        for line in f:
                            if not line.startswith('#') and line.strip():
                                status_file.write(line)
                    status_file.write('\n')

    def remove(self, fn):
        self._print_verbose(f'Remove local file {fn}')
        os.remove(fn)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backup manager using MinIO.')
    parser.add_argument('--backup', action='store_true', help='Execute backup and upload.')
    parser.add_argument('--list', action='store_true', help='List objects and prompt for download.')
    parser.add_argument('--download', metavar='OBJECT_NAME', type=str, help='Directly download specified object.')
    parser.add_argument('--with-status', action='store_true', help=f'Save status to {STATUS_FILE_PATH}')
    parser.add_argument('--enc-text', metavar='TEXT', type=str, help='Encrypto text')
    parser.add_argument('--enc-key', metavar='key', type=str, help='Encrypto key')
    parser.add_argument('--tar', action='store_true', help='use tar instead of zip, disable encrypt')
    parser.add_argument('--dereference', action='store_true', help='follow symlinks')
    parser.add_argument('--verbose', action='store_true', help='Display verbose output.')

    args = parser.parse_args()

    if args.enc_text:
        for txt in args.enc_text.split():
            encrypto(string=txt, key=args.enc_key)
        exit(0)

    if DECRYPTO is True:
        key = DECRYPTO_KEY
        while True:
            try:
                for x in OSS_CONFIGS:
                    for k in ['url', 'access_key', 'secret_key']:
                        x[k] = decrypto(x[k], key)
                break
            except Exception as e:
                key = getpass.getpass('DECRYPTO_KEY is not correct, please input again: ')

    oss_instances = []
    for oss_config in OSS_CONFIGS:
        ossi = OssManger(verbose=args.verbose, **oss_config)
        if ossi.is_connected:
            oss_instances.append(ossi)
    if len(oss_instances) == 0:
        print('No available oss server!')
        exit(1)
    ossi_main = oss_instances[0]

    if args.backup:
        pk = Package(verbose=args.verbose)
        if args.with_status:
            pk.save_status(commands=STATUS_COMMANDS, status_file_path=STATUS_FILE_PATH)
            SOURCE_PATH.append(STATUS_FILE_PATH)
        fn = pk.pack_backup(source_path=SOURCE_PATH, source_exclude=SOURCE_EXCLUDE, tar=args.tar,
                            zip_password=ZIP_PASSWORD, dereference=args.dereference)
        for ossi in oss_instances:
            ossi.upload_object(remote_dir=client_name, local_file_path=fn)
            ossi.delete_old_objects(
                remote_dir=client_name, days_to_retain=DAYS_TO_RETAIN, min_count_to_keep=MIN_COUNT_TO_KEEP)
        pk.remove(fn)
    elif args.list:
        ossi_main.prompt_for_download(remote_dir=client_name)
    elif args.download:
        ossi_main.download_object(args.download)
