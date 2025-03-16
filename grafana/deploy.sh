# Deploy observability stack
helm repo add grafana https://grafana.github.io/helm-charts
helm upgrade --install monitoring grafana/lgtm-distributed -n monitoring --create-namespace --atomic --wait -f grafana/lgtm-distributed.yaml
helm upgrade --install k8s-monitoring grafana/k8s-monitoring -n monitoring --create-namespace --atomic --wait -f grafana/k8s-monitoring.yaml