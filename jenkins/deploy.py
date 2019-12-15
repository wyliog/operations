#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import paramiko
import os
import ruamel.yaml
import shutil
import sys
import argparse
import time


class SSHTools:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = int(port)

    def exec_cmd(self, cmd):
        try:
            # 初始化ssh client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # 建立连接
            ssh.connect(hostname=self.host, port=self.port, username=self.username, password=self.password, timeout=15)
            # 执行命令
            logging.warning(cmd)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            ret = stderr.read().decode()
            if not ret:
                logging.warning(stdout.read().decode())
            else:
                logging.error(ret)
                sys.exit(1)
            # 输出结果
            ssh.close()
        except Exception as e:
            logging.warning("%s exec error\n %s" % (self.host, e))
            sys.exit(1)

    def __get_all_files_in_local_dir(self, local_dir):
        # 保存所有文件的列表
        all_files = list()

        # 获取当前指定目录下的所有目录及文件，包含属性值
        files = os.listdir(local_dir)
        for x in files:
            # local_dir目录中每一个文件或目录的完整路径
            filename = os.path.join(local_dir, x)
            # 如果是目录，则递归处理该目录
            if os.path.isdir(x):
                all_files.extend(self.__get_all_files_in_local_dir(filename))
            else:
                all_files.append(filename)
        return all_files

    def sftp_dir_file(self, local_dir, remote_dir):
        try:
            # 初始化
            t = paramiko.Transport((self.host, self.port))
            t.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(t)
            # 去掉末尾/
            if remote_dir[-1] == '/':
                remote_dir = remote_dir[0:-1]
            logging.warning("%s \t %s" % (self.host, self.port))
            all_files = self.__get_all_files_in_local_dir(local_dir)
            logging.warning("%s \t %s" % (self.host, self.port))
            # 遍历上传
            for file in all_files:
                filename = os.path.split(file)[-1]
                remote_filename = remote_dir + '/' + filename
                logging.warning(u'%s\t transporting...' % filename)
                sftp.put(file, remote_filename)
            sftp.close()
        except Exception as e:
            logging.warning("%s sftp error\n %s" % (self.host, e))

    def sftp_file(self, local_file_path, remote_file_path):
        try:
            t = paramiko.Transport((self.host, self.port))
            t.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(t)
            logging.warning(u'%s\t transporting...' % local_file_path)
            sftp.put(local_file_path, remote_file_path)
            t.close()
        except Exception as e:
            logging.warning("%s sftp error\n %s" % (self.host, e))


class DeployToKube:
    def __init__(self, ssh_client, environment, service_name, tag, helm_repo_name='fanoai'):
        self.ssh_client = ssh_client
        self.environment = environment
        self.service_name = service_name
        self.tag = tag
        self.helm_repo_name = helm_repo_name
        if self.environment:
            self.value_file = "values-%s.yaml" % self.environment
            self.helm_ns = "%s-%s" % (self.service_name, self.environment)
            self.namespace = self.environment
        else:
            self.value_file = "values.yaml"
            self.helm_ns = self.service_name
            self.namespace = 'default'

    def __yaml_modify_config(self, file_name_value='values.yaml'):
        try:
            yaml = ruamel.yaml.YAML()
            yaml.preserve_quotes = True
            # yaml.explicit_start = True
            # 修改values
            with open(file_name_value) as stream:
                data = yaml.load(stream)
            image = data['image']
            image.update(dict(tag=self.tag))

            with open(file_name_value + '-new', 'wb') as stream:
                yaml.dump(data, stream)
            shutil.move(file_name_value + "-new", file_name_value)
            # 修改chart
            with open("Chart.yaml") as f:
                data = yaml.load(f)
            data['appVersion'] = self.tag
            old_version = data['version'].split('.')
            old_version[len(old_version) - 1] = str(int(old_version[len(old_version) - 1]) + 1)
            new_version = ".".join(old_version)
            data['version'] = new_version
            with open("Chart.yaml" + '-new', 'wb') as stream:
                yaml.dump(data, stream)
            shutil.move("Chart.yaml" + "-new", "Chart.yaml")
        except Exception as e:
            logging.warning(e)

    @staticmethod
    def __local_exec_cmd(cmd):
        try:
            logging.warning(cmd)
            exec_cmd_stdout = os.popen(cmd)
            logging.warning(exec_cmd_stdout.read())

        except Exception as e:
            logging.warning(e)

    def helm_push(self, docker_username, docker_password):
        try:
            self.__local_exec_cmd("helm repo update && rm -rf %s" % self.service_name)
            self.__local_exec_cmd("helm fetch %s/%s --untar" % (self.helm_repo_name, self.service_name))
            # 修改文件
            os.chdir(self.service_name)
            logging.warning(os.getcwd())
            self.__yaml_modify_config("%s" % self.value_file)
            # push 到helm 仓库
            self.__local_exec_cmd("helm push . -u %s -p %s  %s" % (docker_username, docker_password,
                                                                   self.helm_repo_name))
        except Exception as e:
            logging.warning(e)

    def deploy(self):
        pass

    def upgrade(self, helm_dir):
        try:

            self.ssh_client.exec_cmd("helm repo update && rm -rf /tmp/%s" % self.service_name)
            time.sleep(1)
            self.ssh_client.exec_cmd(
                "cd %s && helm fetch %s/%s --untar" % (helm_dir, self.helm_repo_name, self.service_name))
            time.sleep(2)
            self.ssh_client.exec_cmd("cd %s/%s && sleep 2 && helm upgrade --tls -f %s %s  ." % (
                    helm_dir, self.service_name, self.value_file, self.helm_ns))
            time.sleep(5)
            self.get_upgrade_result()
        except Exception as e:
            logging.warning(e)

    def get_upgrade_result(self):
        get_status_cmd = '''
        for i in {1..60}
        do
           if kubectl get po -n %s|grep %s|grep -v Running >/dev/null
           then
              Status="Status: $(kubectl get po -n %s|grep %s|grep -v Running|awk '{print $3}')"
              ret=false
              sleep 5
           else
              Status="Status: $(kubectl get po -n %s|grep %s|awk '{print $3}')"
              ret=true
              break
           fi
        done
        image=`kubectl get deploy %s -o yaml -n %s |grep image:|awk '$1=$1'`
        if ${ret}
        then
         echo "Upgrade Success!"
         echo "${Status}"
         echo "${image}"
        else
         echo "Upgrade Eroor,Please check!"
         echo "${Status}"
         echo "${image}"
        fi
        ''' % (self.namespace, self.service_name, self.namespace, self.service_name, self.namespace,
               self.service_name,self.service_name,self.namespace)
        try:
            self.ssh_client.exec_cmd(get_status_cmd)
        except Exception as e:
            logging.warning(e)


def main():
    tag = os.environ.get("Tag")
    docker_username = os.environ.get("UserName")
    docker_password = os.environ.get("Password")
    k8s_username = os.environ.get("k8s_username")
    k8s_password = os.environ.get("k8s_password")
    work_dir = os.environ.get("WORKSPACE")
    # 获取参数值
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", nargs='+', type=str)
    parser.add_argument("--port", nargs='+', type=str)
    parser.add_argument("--environment", nargs='+', type=str)
    parser.add_argument("--serviceName", nargs='+', type=str)
    parser.add_argument("--helmRepoName", nargs='+', type=str)
    args = parser.parse_args()
    try:
        host = args.host[0]
        port = args.port[0]
        environment = args.environment[0]
        service_name = args.serviceName[0]
        helm_repo_name = args.helmRepoName[0]
    except Exception as e:
        parser.print_help()
        logging.warning(e)
        sys.exit(1)
    try:
        os.chdir("%s/%s" % (work_dir, service_name))
        logging.warning(os.getcwd())
        if not tag:
            tag = os.popen("git describe --tags `git rev-list --tags --max-count=1`").read().strip('\n')
        ssh_client = SSHTools(host=host, port=port, username=k8s_username, password=k8s_password)
        deploy = DeployToKube(ssh_client, environment=environment, service_name=service_name, tag=tag,
                              helm_repo_name=helm_repo_name)
        deploy.helm_push(docker_username=docker_username, docker_password=docker_password)
        deploy.upgrade("/tmp")
    except Exception as e:
        logging.warning(e)


if __name__ == '__main__':
    main()
