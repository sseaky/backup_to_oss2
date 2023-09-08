#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ChatGPT, Seaky

import argparse
import os
import re
import subprocess
import pytz
from minio import Minio
import socket
from datetime import datetime, timedelta

from config import (BUCKET, ACCESS_KEY, SECRET_KEY, URL, CLIENT_NAME, LotageBackupDays, STATUS_FILE,
                    MinPresaveBackup, ZIP_PASSWORD, SOURCE, SOURCE_EXCLUDE, STATUS_COMMANDS)


def get_client_name():
    hostname = socket.gethostname()
    default_interface = subprocess.getoutput("ip route | grep default | awk '{print $5}' | head -1")
    ip_address = subprocess.getoutput(
        f'ip addr show {default_interface} | grep \'inet \' | awk \'{{print $2}}\' | cut -d/ -f1')
    if not re.search('^[\d.]+$', ip_address):
        raise 'get default ip address fail!'
    return f'{hostname}_{ip_address}'


class BackupManager:
    def __init__(self, verbose=False):
        self.url = URL
        secure = True if URL.startswith('https') else False
        endpoint = re.sub('http[s]://', '', URL, re.I)
        self.client = Minio(endpoint, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=secure)
        print(f'Connect {self.url}')
        self.source = [x.strip() for x in SOURCE.strip().split('\n') if x]
        self.source_exclude = [x.strip() for x in SOURCE_EXCLUDE.strip().split('\n') if x]
        self.client_name = CLIENT_NAME or get_client_name()
        self.verbose = verbose

    def _print_verbose(self, message):
        if self.verbose:
            print(message)

    def _safe_subprocess_run(self, command):
        self._print_verbose(f'RUN: {" ".join(command)}')
        output = subprocess.getoutput(' '.join(command))
        return output

    def create_bucket(self, bucket_name):
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            self._print_verbose(f'Bucket {bucket_name} created successfully')

    def upload_object(self, bucket_name, object_name, file_path):
        """Upload the specified file to the specified bucket."""
        self._print_verbose(f'Uploading {file_path} to {bucket_name}/{object_name}')
        result = self.client.fput_object(bucket_name, object_name, file_path)
        self._print_verbose(f'Uploaded as {result.object_name} with ETag: {result.etag}')

    def _prompt_for_download(self, objs):
        # Number the objects
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
                    self.download_object(BUCKET, objs[choice_num - 1].object_name)
                    break
                else:
                    print(f"Please enter a number between 1 and {len(objs)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit.")

    def download_object(self, bucket_name, object_name):
        file_path = object_name.split('/')[-1]
        self.client.fget_object(bucket_name, object_name, file_path)
        self._print_verbose(f'Downloaded {object_name} from bucket {bucket_name} to {file_path}')

    def delete_old_objects(self, bucket_name, prefix, days_to_retain, min_count_to_keep):
        current_time_with_tz = datetime.now(pytz.timezone('Asia/Shanghai'))
        objs_to_delete = []
        objects = sorted(self.client.list_objects(bucket_name, prefix=prefix), key=lambda x: x.last_modified)

        for obj in objects:
            if len(objects) - len(objs_to_delete) <= min_count_to_keep:
                break
            if current_time_with_tz - obj.last_modified > timedelta(days=days_to_retain):
                objs_to_delete.append(obj.object_name)

        for obj_name in objs_to_delete:
            self.client.remove_object(bucket_name, obj_name)
            self._print_verbose(f'Deleted {obj_name} from bucket {bucket_name}')

    def pack_backup(self):
        # Define tar and zip names
        current_datetime = datetime.now().strftime('%y%m%d%H%M%S')
        tar_name = f'autobackup_{current_datetime}.tar'
        zip_name = f'{tar_name}.zip'
        # Create tar
        tar_command = ['tar', 'cf', tar_name] + ['--exclude=' + pattern for pattern in self.source_exclude] + self.source
        self._safe_subprocess_run(tar_command)
        # Zip with password
        zip_command = ['zip', '-P', ZIP_PASSWORD, zip_name, tar_name]
        self._safe_subprocess_run(zip_command)
        # Remove tar file
        os.remove(tar_name)
        return zip_name  # Return zip_name for further processing

    def save_status(self, status_file_path):
        with open(status_file_path, 'w') as status_file:
            for cmd in STATUS_COMMANDS:
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


    def perform_backup(self):
        self.save_status(STATUS_FILE)
        zip_name = self.pack_backup()
        object_path = f'{self.client_name}/{zip_name}'
        self.create_bucket(BUCKET)
        self.upload_object(BUCKET, object_path, zip_name)
        os.remove(zip_name)
        self.delete_old_objects(BUCKET, f'{self.client_name}/', LotageBackupDays, MinPresaveBackup)

    def run(self, backup, list_objects, download_object):
        if backup:
            self.perform_backup()
        elif list_objects:
            objs = list(self.client.list_objects(BUCKET, f'{self.client_name}/'))
            self._prompt_for_download(objs)
        elif download_object:
            self.download_object(BUCKET, download_object)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backup manager using MinIO.')
    parser.add_argument('--backup', action='store_true', help='Execute backup and upload.')
    parser.add_argument('--list', action='store_true', help='List objects and prompt for download.')
    parser.add_argument('--download', metavar='OBJECT_NAME', type=str, help='Directly download specified object.')
    parser.add_argument('--verbose', action='store_true', help='Display verbose output.')

    args = parser.parse_args()

    if not any([args.backup, args.list, args.download]):
        print("At least one action (--backup, --list, --download) must be specified.")
        exit(1)

    manager = BackupManager(verbose=args.verbose)
    manager.run(args.backup, args.list, args.download)
