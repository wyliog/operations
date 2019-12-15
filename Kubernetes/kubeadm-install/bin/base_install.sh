#!/bin/bash
    
function setSysConfig(){
    
 yum update -y
 yum install wget zip unzip -y
#disable Firewalld
    systemctl stop firewalld
    systemctl disable firewalld
#Disable Selinux
    setenforce 0
    cp -p /etc/selinux/config /etc/selinux/config.bak
    sed -i "s/^SELINUX=.*/SELINUX=disabled/g" /etc/selinux/config
#Disable Swap
    swapoff -a
    cp -p /etc/fstab /etc/fstab.bak
    sed -i "/swap/s/^/#/g" /etc/fstab
    mount -a
#Setup iptables
    modprobe br_netfilter
cat <<EOF >  /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-arptables = 1
vm.max_map_count=262144
EOF
    sysctl -p /etc/sysctl.d/k8s.conf
}

function installNfsClient(){
    yum install nfs-utils -y
    sudo systemctl enable rpcbind
    sudo systemctl start rpcbind

}

function installDocker(){

#remove old  docker
  sudo yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-selinux \
                  docker-engine-selinux \
                  docker-engine  -y
#install lvm
   sudo yum install -y yum-utils device-mapper-persistent-data lvm2
#set repo
   sudo yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
#install docker
   yum install docker-ce-18.09.6-3.el7.x86_64 -y
   systemctl enable docker
   systemctl start docker

#configure docker 
cat > /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
EOF
  sudo systemctl daemon-reload
  sudo systemctl restart docker

}
    
function installK8s(){
#set k8s source
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF

  yum clean all
  yum makecache -y 

  #install k8s
  yum install -y kubelet-1.14.3 kubeadm-1.14.3 kubectl-1.14.3 kubernetes-cni-0.7.5
  systemctl enable kubelet && systemctl start kubelet
  #set cgroup driver
  #sed -i "s/cgroup-driver=systemd/cgroup-driver=cgroupfs/g" /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
  #systemctl daemon-reload
  systemctl restart kubelet

}

main(){
  setSysConfig
  installNfsClient
  installDocker
  installK8s
}
main
