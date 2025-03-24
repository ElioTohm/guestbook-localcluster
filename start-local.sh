#!/bin/bash
. $(pwd)/init.sh

# https://kind.sigs.k8s.io/docs/user/local-registry/
set -o errexit

print_headline "create registry container unless it already exists"
reg_name='kind-registry'
reg_port='5000'
if [ "$(docker inspect -f '{{.State.Running}}' "${reg_name}" 2>/dev/null || true)" != 'true' ]; then
  docker run \
    -d --restart=always -p "127.0.0.1:${reg_port}:5000" --name "${reg_name}" \
    registry:2
fi

print_header "create a cluster with the local registry enabled in containerd"
# also add a port mapping for the ingress https://kind.sigs.k8s.io/docs/user/ingress/
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:${reg_port}"]
    endpoint = ["http://${reg_name}:5000"]
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF

print_header "switch kubectl context to the local cluster"
kubectl config use-context kind-kind

print_header "connect the registry to the cluster network if not already connected"
if [ "$(docker inspect -f='{{json .NetworkSettings.Networks.kind}}' "${reg_name}")" = 'null' ]; then
  docker network connect "kind" "${reg_name}"
fi

# Document the local registry
# https://github.com/kubernetes/enhancements/tree/master/keps/sig-cluster-lifecycle/generic/1755-communicating-a-local-registry
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:${reg_port}"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF

print_header "Setup Ingress"
kubectl apply -f "https://raw.githubusercontent.com/kubernetes/ingress-nginx/refs/heads/main/deploy/static/provider/kind/deploy.yaml"
print_header "waiting for nginx ingress installation to be complete"
kubectl wait pod -l app.kubernetes.io/component=controller,app.kubernetes.io/name=ingress-nginx --for=condition=Ready --namespace=ingress-nginx --timeout=300s

print_header "Install Grafana stack LGTM distriuted"
./grafana/deploy.sh

print_headline "Build localy the images and tag"
docker build src/backend/ -t localhost:5000/python-guestbook-backend
docker build src/frontend/ -t localhost:5000/python-guestbook-frontend

print_header "Push images to local registery"

docker pull mongo:4
docker tag mongo:4 localhost:5000/mongo:4
docker push localhost:5000/python-guestbook-backend
docker push localhost:5000/python-guestbook-frontend
docker push localhost:5000/mongo:4

print_header "Apply modified yaml files to pull image from local-registry"
helm upgrade --install python-guestbook ./src/chart/ -n default

print_header "admin password: $(kubectl get secret --namespace monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 --decode)"

