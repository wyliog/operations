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
    pause:${KUBE_PAUSE_VERSION}
    coredns:${CORE_DNS_VERSION})
    for image  in  ${images[@]};
    do
       docker pull ${image_path}/$image
       docker tag ${image_path}/$image $GCR_URL/$image
       docker rmi ${image_path}/$image 
    done
}

main(){
    getImages
}
main
