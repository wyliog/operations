import requests
import logging
import os


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


class HKDockerTools:
    def __init__(self, hk_username, hk_password, hk_docker_registry):
        self.username = hk_username
        self.password = hk_password
        self.hk_docker_registry = hk_docker_registry

    def get_image_token(self):
        auth = ('infra', 'fanolabs')
        headers = {
            'Content-Type': 'application/json',
        }
        get_token_url = 'https://%s/docker-auth?service=registry' % self.hk_docker_registry
        response = requests.get(get_token_url, headers=headers, auth=auth)
        token = response.json()["token"]
        return token

    def get_file_token(self):
        auth = (self.username, self.password)
        headers = {
            'Content-Type': 'application/json',
        }
        get_token_url = 'https://%s/resource-auth' % self.hk_docker_registry
        response = requests.get(get_token_url, headers=headers, auth=auth)
        token = response.json()["token"]
        return token

    def get_tag_token(self, repo_name):
        auth = (self.username, self.password)
        headers = {
            'Content-Type': 'application/json',
        }
        get_token_url = 'https://%s/docker-auth?service=registry&scope=repository:%s:pull' % (self.hk_docker_registry,
                                                                                              repo_name)
        response = requests.get(get_token_url, headers=headers, auth=auth)
        token = response.json()["token"]
        return token

    def get_docker_hub(self):
        data = '{"username": "%s" , "password": "%s" }' % (self.username, self.password)
        headers = {
            'Content-Type': 'application/json',
        }
        url = 'https://%s/v2/users/login/' % self.hk_docker_registry
        response = requests.post(url, headers=headers, data=data)
        print(response)
        token = response.json()['token']
        logging.warning(token)
        headers = {
            'Authorization': 'JWT %s' % token,
        }
        url = 'https://%s/v2/repositories/wyliog?page_size=100000' % self.hk_docker_registry
        response1 = requests.get(url, headers=headers)
        for i in response1.json()['results']:
            print(i['name'])
            # url1 = 'https://hub.docker.com/v2/repositories/%s/%s/tags/?page_size=10000' % (self.username, i['name'])
            # r = requests.get(url1, headers=headers)
            # print(r.text)

    def get_image(self):
        token = self.get_image_token()
        url = 'https://%s/v2/_catalog' % self.hk_docker_registry
        headers = {
            'Content-Type': 'application/json',
            'authorization': 'Bearer %s' % token,
        }
        response = requests.get(url, headers=headers)
        return response.json()['repositories']

    def query_tag(self, username, password, registry, repo, service_name, tag):
        ret_flag = 1
        auth = (username, password)
        headers = {
            'Content-Type': 'application/json',
        }
        url = 'https://%s/api/repositories/%s/%s/tags' % (registry, repo, service_name)
        response = requests.get(url, headers=headers, auth=auth)
        for i in response.json():
            if i['name'] == tag:
                logging.warning("%s:%s image tag exsits" % (service_name, tag))
                ret_flag = 0
                break
            else:
                ret_flag = 1
        return ret_flag

    def get_image_tag(self, username, password, registry, repo):
        list_tag = []
        for i in self.get_image():
            token = self.get_tag_token(i)
            url = 'https://%s/v2/%s/tags/list' % (self.hk_docker_registry, i)
            headers = {
                'Content-Type': 'application/json',
                'authorization': 'Bearer %s' % token,
            }
            response = requests.get(url, headers=headers)
            if 'name' in response.json().keys():
                list_tag.append(response.json())
        for i in list_tag:
            for j in i['tags']:
                if self.query_tag(username, password, registry, repo, i['name'], j) or j == 'master':
                    push_old_url = "%s/%s:%s" % (self.hk_docker_registry, i['name'], j)
                    push_new_url = "%s/%s/%s:%s" % (registry, repo, i['name'], j)
                    print(push_new_url)
                    logging.warning("start pull :%s" % push_old_url)
                    os.system('docker pull %s' % push_old_url)
                    os.system('docker tag %s %s' % (push_old_url, push_new_url))
                    os.system('docker push %s' % push_new_url)
                    logging.warning("push done : %s" % push_new_url)


def main():
    console_out("/var/log/images.log")
    username = 'xxx'
    password = 'xxx'
    registry = 'xxx.xxx.xxx.xxx'
    repo = 'xxx'
    hk_docker_registry = 'xxx.xxx.xxx.xxx'
    # docker_registry = 'hub.docker.com'
    hk_username = 'xxx'
    hk_password = 'xxx'
    docker_tools = HKDockerTools(hk_username, hk_password, hk_docker_registry)
    docker_tools.get_image_tag(sz_username, sz_password, sz_registry, sz_repo)


if __name__ == '__main__':
    main()
