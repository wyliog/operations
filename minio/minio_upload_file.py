#! _*_ coding:utf-8 _*_
from minio import Minio
from minio.error import ResponseError
import os
import logging
import hashlib
import time
import shutil
import tarfile


def console_out(log_filename):
    # Define a Handler and set a format which output to file
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',
        datefmt='%Y-%m-%d %A %H:%M:%S',
        filename=log_filename,
        filemode='a')
    # Define a Handler and set a format which output to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s  %(filename)s : %(levelname)s  %(message)s')
    console.setFormatter(formatter)
    # Create an instance
    logging.getLogger().addHandler(console)


def upload_minio_file(minio_host, access_key, secret_key, bucket_name, file, minio_path=""):
    # 创建minio连接
    minioClient = Minio(minio_host,
                        access_key=access_key,
                        secret_key=secret_key,
                        secure=False)
    if not minioClient.bucket_exists(bucket_name):
        minioClient.make_bucket(bucket_name)
    # 上传文件
    file_name = os.path.basename(file)
    try:
        logging.info("start upload file: %s" % file)
        with open(file, 'rb') as file_data:
            file_stat = os.stat(file)
            minioClient.put_object(bucket_name, minio_path + file_name,
                                   file_data, file_stat.st_size)
        logging.info("file upload end : %s" % file)
    except ResponseError as err:
        logging.error('file upload error: %s' % file)
        logging.error(err)


# 计算md5值
def md5sum(filename, blocksize=65536):
    hash_value = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash_value.update(block)
    f.close()
    return hash_value.hexdigest()


def upload_file(dir_path, minio_host, access_key, secret_key, bucket_name):
    os.chdir(dir_path)
    for root, dirs, files in os.walk("cmhk"):
        for file_name in files:
            # 上传tar.gz
            if os.path.splitext(file_name)[1] == '.gz':
                hash1 = md5sum(os.path.join(root, file_name))
                time.sleep(5)
                hash2 = md5sum(os.path.join(root, file_name))
                if hash1 == hash2:
                    upload_minio_file(minio_host, access_key, secret_key, bucket_name,
                                      os.path.join(dir_path, root, file_name),
                                      root + "/")
                else:
                    logging.warning("file in sending.....")


def main():
    ex_dir_path = os.environ.get("KM_PATH")
    console_out('upload_minio.log')
    minio_host = os.environ.get("MINIO_HOST")
    access_key = os.environ.get("ACCESS_KEY")
    secret_key = os.environ.get("SECRET_KEY")
    bucket_name = os.environ.get("BUCKET_NAME")
    dir_path = os.environ.get("VOICE_DIR_PATH")
    while True:
        try:
            upload_file(dir_path, minio_host, access_key, secret_key, bucket_name)
            time.sleep(10)
        except Exception as e:
            logging.exception(e)


if __name__ == '__main__':
    main()
