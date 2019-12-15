#!/bin/bash
SCRIPT_PATH=$(cd "$(dirname "$0")";pwd)
INSTALL_PATH=$(cd "$SCRIPT_PATH";cd ../;pwd)
. ${INSTALL_PATH}/install.conf
#docker login -u ${docker_user} -p ${docker_password} ${docker_registry}
#if [[ $? == 1 ]]
#then
#    echo "Docker Password or Username Error"
#    exit 1
#fi
function getImages(){
    images=(kube-proxy:${KUBE_VERSION}
    kube-scheduler:${KUBE_VERSION}
    kube-controller-manager:${KUBE_VERSION}
    kube-apiserver:${KUBE_VERSION}
    pause:${KUBE_PAUSE_VERSION}
    etcd:${ETCD_VERSION}
    coredns:${CORE_DNS_VERSION})
    
    for image  in  ${images[@]};
    do
      docker pull ${image_path}/$image
      docker tag ${image_path}/$image $GCR_URL/$image
      docker rmi ${image_path}/$image
    done
}

function installK8s(){
    kubeadm reset -f
    kubeadm init --kubernetes-version=${KUBE_VERSION} --pod-network-cidr=10.244.0.0/16
    mkdir -p $HOME/.kube
    sudo cp /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config
    kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
}
#function configMaster(){
#    cp /etc/kubernetes/manifests/kube-apiserver.yaml ./kube-apiserver.yaml-bak
#    sed -i '/--secure-port=/a\    - --service-node-port-range=80-65535' /etc/kubernetes/manifests/kube-apiserver.yaml
#    systemctl restart kubelet
#    sleep 20
#    kubectl taint nodes --all node-role.kubernetes.io/master:NoSchedule-
#    kubectl label node --all node-role.kubernetes.io/master-
#}
main(){
    getImages
    installK8s
    sleep 20
}
main

