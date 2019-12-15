#!/bin/bash
FILE_PATH=$(pwd)
CSR=${FILE_PATH}/user-csr.json
SSL_PATH="/etc/kubernetes/ssl"
SSL_FILES=(ca-key.pem ca.pem ca-config.json)
CERT_FILES=(${USER}.csr $USER-key.pem ${USER}.pem)
NAMESPACE=default
usage()
{
cat << EOF
usage: $0 options
This script create a kubernetes rabc user
OPTIONS:
   -h      Show this message
   -a      api address
   -u      UserName
   -n      namespace
eg:
   sh create_user.sh -a https://localhost:6443 -u test -n test
EOF
}


# 创建用户的csr文件
function createCSR(){
cat>$CSR<<EOF
{
  "CN": "USER",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "CN",
      "ST": "BeiJing",
      "L": "BeiJing",
      "O": "k8s",
      "OU": "System"
    }
  ]
}
EOF

sed -i "s/USER/$USER/g" $CSR
}

function ifExist(){
  if [ ! -f "$SSL_PATH/$1" ]; then
      echo "$SSL_PATH/$1 not found."
      exit 1
  fi
}

main(){
  # 判断集群ca证书是否存在
  for f in ${SSL_FILES[@]};
  do
      echo "Check if ssl file $f exist..."
      ifExist $f
      echo "OK"
  done
  # 创建用户证书
  createCSR
  echo "$CSR created"
  echo "Create user's certificates and keys..."
  cd $SSL_PATH
  cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes $CSR| cfssljson -bare $USER
  cd -

  # 设置集群参数
  kubectl config set-cluster kubernetes \
  --certificate-authority=${SSL_PATH}/ca.pem \
  --embed-certs=true \
  --server=${KUBE_APISERVER} \
  --kubeconfig=${USER}.kubeconfig

  # 设置客户端认证参数
  kubectl config set-credentials $USER \
  --client-certificate=$SSL_PATH/${USER}.pem \
  --client-key=$SSL_PATH/${USER}-key.pem \
  --embed-certs=true \
  --kubeconfig=${USER}.kubeconfig

  # 设置上下文参数
  kubectl config set-context kubernetes \
  --cluster=kubernetes \
  --user=$USER \
  --namespace=${NAMESPACE} \
  --kubeconfig=${USER}.kubeconfig

  # 设置默认上下文
  kubectl config use-context kubernetes --kubeconfig=${USER}.kubeconfig
  # 绑定角色
  kubectl create rolebinding ${USER}-admin-binding --clusterrole=admin --user=$USER --namespace=${NAMESPACE} --serviceaccount=$USER:default
  # kubectl config get-contexts
  echo "Congratulations!"
  echo "Your kubeconfig file is ${USER}.kubeconfig"
}

while getopts “h:a:u:n:” OPTION
do
  case $OPTION in
    h)
      usage
      exit 1
      ;;
    a)
      KUBE_APISERVER=$OPTARG
      ;;
    u)
      USER=$OPTARG
      ;;
    n)
      NAMESPACE=$OPTARG
      ;;
    ?)
      usage
      exit
    ;;
  esac
done

main