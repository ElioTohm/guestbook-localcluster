#!/bin/bash
. $(pwd)/init.sh

print_headline "Installing victoria-metrics-k8s-stack"
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm upgrade --install vmks vm/victoria-metrics-k8s-stack -f victoriametrics/victoria-metrics-k8s-stack.yaml -n vmks --create-namespace --atomic

print_headline "Installing victoria-logs"
helm upgrade --install vls vm/victoria-logs-single -n vls --create-namespace -f victoriametrics/victoria-logs-single.yaml

print_headline "Installing otlp"
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
helm upgrade -i otel open-telemetry/opentelemetry-collector -f victoriametrics/otel-values.yaml -n otlp --create-namespace

print_headline "Installing guestbook with victoriametrics"
helm upgrade --install python-guestbook ./src/chart/ -n default -f victoriametrics/vm.values.yaml

print_header "admin password: $(kubectl get secret -n vmks vmks-grafana -o jsonpath="{.data.admin-password}" | base64 --decode)"

